import datetime
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.file import File
from app.models.policy import LifecyclePolicy
from app.crud.base import update_file_backend, create_migration_entry, complete_migration_entry, log_activity
from app.adapters.service import storage_service

@celery_app.task(name="app.tasks.migration.migrate_file_task")
def migrate_file_task(file_id: int, dest_tier: str) -> bool:
    print(f"[INFO] Celery starting migration for File ID {file_id} to tier {dest_tier}")
    db = SessionLocal()
    try:
        # 1. Fetch file record
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            print(f"[ERROR] File ID {file_id} not found in database.")
            return False
            
        if file.status == "deleted":
            print(f"[WARNING] File ID {file_id} is deleted. Aborting migration.")
            return False
            
        if file.status == "migrating":
            print(f"[WARNING] File ID {file_id} is already undergoing migration. Aborting concurrent attempt.")
            return False
            
        source_tier = file.current_tier
        if source_tier.lower() == dest_tier.lower():
            print(f"[INFO] File ID {file_id} is already in the target tier {dest_tier}. No action needed.")
            return True
            
        # 2. Lock file status
        file.status = "migrating"
        db.commit()
        
        # 3. Create Migration history entry
        # Map dest_tier to backend
        dest_backend = "minio"
        if dest_tier == "warm":
            dest_backend = "seaweedfs"
        elif dest_tier == "archive":
            dest_backend = "scality"
            
        migration_entry = create_migration_entry(
            db,
            file_id=file.id,
            source_backend=file.current_backend,
            dest_backend=dest_backend,
            source_tier=source_tier,
            dest_tier=dest_tier
        )
        
        # Log migration start
        log_activity(
            db,
            user_id=file.owner_id,
            action="migration_start",
            file_id=file.id,
            details=f"Starting migration of '{file.name}' from {source_tier} to {dest_tier}."
        )
        
        # 4. Perform migration transfer
        try:
            # Performs download -> upload -> destination checksum verification -> source deletion
            storage_service.migrate_file(file.uuid, source_tier, dest_tier, file.checksum)
        except Exception as e:
            # Log failure in database
            file.status = "active"
            complete_migration_entry(db, migration_entry.id, "failed", error_message=str(e))
            log_activity(
                db,
                user_id=file.owner_id,
                action="migration_failed",
                file_id=file.id,
                details=f"Migration of '{file.name}' from {source_tier} to {dest_tier} failed: {str(e)}."
            )
            db.commit()
            print(f"[ERROR] Migration failed for File ID {file_id}: {str(e)}")
            return False
            
        # 5. Migration succeeded. Update file record
        update_file_backend(db, file_id, new_backend=dest_backend, new_tier=dest_tier)
        file.status = "active"
        
        complete_migration_entry(db, migration_entry.id, "success")
        
        log_activity(
            db,
            user_id=file.owner_id,
            action="migration_success",
            file_id=file.id,
            details=f"Successfully migrated '{file.name}' from {source_tier} to {dest_tier} (Active tier: {dest_tier})."
        )
        
        db.commit()
        print(f"[SUCCESS] Migrated File ID {file_id} to tier {dest_tier} successfully.")
        return True
        
    except Exception as e:
        print(f"[FATAL] System error in migration task for File ID {file_id}: {str(e)}")
        return False
    finally:
        db.close()

@celery_app.task(name="app.tasks.migration.apply_lifecycle_policies_task")
def apply_lifecycle_policies_task() -> int:
    print("[INFO] Evaluating Active Lifecycle Policies against stored files...")
    db = SessionLocal()
    migrations_triggered = 0
    try:
        # Get active policies
        policies = db.query(LifecyclePolicy).filter(LifecyclePolicy.is_active == True).all()
        
        for policy in policies:
            # Compute age threshold
            # Upload date must be older than threshold to qualify for transition
            threshold_date = datetime.datetime.utcnow() - datetime.timedelta(days=policy.duration_days)
            
            # Query files in matching tier that are active and exceed threshold
            files_to_migrate = db.query(File).filter(
                File.current_tier == policy.source_tier,
                File.status == "active",
                File.upload_date <= threshold_date
            ).all()
            
            print(f"[INFO] Policy '{policy.name}' ({policy.source_tier} -> {policy.dest_tier}, age > {policy.duration_days} days): Found {len(files_to_migrate)} qualifying files.")
            
            for file in files_to_migrate:
                # Trigger individual migration asynchronously (inline in eager mode)
                migrate_file_task.delay(file.id, policy.dest_tier)
                migrations_triggered += 1
                
        return migrations_triggered
    except Exception as e:
        print(f"[ERROR] Lifecycle policies execution failed: {str(e)}")
        return 0
    finally:
        db.close()
