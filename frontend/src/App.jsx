import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import axios from 'axios'
import { 
  Server, Database, Activity, HardDrive, RefreshCw, Layers, CheckCircle2, XCircle, 
  LogOut, User as UserIcon, Shield, Folder, FolderPlus, FileText, Image, Video, File, 
  Upload, Trash2, Edit3, ChevronRight, Home, Plus, X, Search, Download, AlertCircle, FileCode,
  BarChart2, Sliders, ToggleLeft, ToggleRight, TrendingUp,
  MoreVertical, FileSpreadsheet, FileAudio, FileArchive, Info, Map, Clock, ArrowRight, 
  FolderOpen, PlusSquare, Eye, Copy, Play, Pause, Loader, ChevronDown
} from 'lucide-react'

// --- ROUTE GUARD HELPERS ---
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}

const GuestRoute = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    )
  }
  if (user) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

// --- POLICY ROW COMPONENT ---
function PolicyRow({ policy, onUpdate }) {
  const parseDuration = (days) => {
    const totalMinutes = Math.round(days * 1440)
    if (totalMinutes === 0) {
      return { value: 0, unit: 'minutes' }
    }
    if (totalMinutes % 1440 === 0) {
      return { value: totalMinutes / 1440, unit: 'days' }
    } else if (totalMinutes % 60 === 0) {
      return { value: totalMinutes / 60, unit: 'hours' }
    } else {
      return { value: totalMinutes, unit: 'minutes' }
    }
  }

  const parsed = parseDuration(policy.duration_days)
  const [val, setVal] = useState(parsed.value)
  const [unit, setUnit] = useState(parsed.unit)
  const [isActive, setIsActive] = useState(policy.is_active)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const p = parseDuration(policy.duration_days)
    setVal(p.value)
    setUnit(p.unit)
    setIsActive(policy.is_active)
  }, [policy])

  const tierLabel = (tier) => {
    if (tier === 'hot') return 'Hot (MinIO)'
    if (tier === 'warm') return 'Warm (SeaweedFS)'
    return 'Archive (Scality S3 Server)'
  }

  const tierColor = (tier) => {
    if (tier === 'hot') return 'text-amber-400'
    if (tier === 'warm') return 'text-cyan-400'
    return 'text-purple-400'
  }

  const handleSave = async () => {
    setSaving(true)
    let days = parseFloat(val)
    if (unit === 'hours') {
      days = days / 24
    } else if (unit === 'minutes') {
      days = days / 1440
    }
    await onUpdate(policy.id, days, isActive)
    setSaving(false)
    setEditing(false)
  }

  const handleToggle = async () => {
    const newActive = !isActive
    setIsActive(newActive)
    let days = parseFloat(val)
    if (unit === 'hours') {
      days = days / 24
    } else if (unit === 'minutes') {
      days = days / 1440
    }
    await onUpdate(policy.id, days, newActive)
  }

  return (
    <div className="p-3 rounded-2xl bg-slate-950/50 border border-slate-900">
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] font-bold text-slate-300">
          <span className={tierColor(policy.source_tier)}>{tierLabel(policy.source_tier)}</span>
          <span className="text-slate-600 mx-1">→</span>
          <span className={tierColor(policy.dest_tier)}>{tierLabel(policy.dest_tier)}</span>
        </div>
        <button
          onClick={handleToggle}
          className="flex items-center gap-1"
          title={isActive ? 'Disable policy' : 'Enable policy'}
        >
          {isActive
            ? <ToggleRight className="w-5 h-5 text-emerald-400" />
            : <ToggleLeft className="w-5 h-5 text-slate-600" />
          }
        </button>
      </div>
      <div className="flex items-center justify-between">
        {editing ? (
          <div className="flex items-center gap-2 flex-1">
            <input
              type="number"
              min="0.0001"
              step="any"
              value={val}
              onChange={(e) => setVal(e.target.value)}
              className="w-16 px-2 py-1 bg-slate-900 border border-slate-800 rounded-lg text-[10px] text-slate-200 font-mono focus:outline-none focus:border-brand-500"
            />
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="px-2 py-1 bg-slate-900 border border-slate-800 rounded-lg text-[10px] text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="days">days</option>
              <option value="hours">hours</option>
              <option value="minutes">minutes</option>
            </select>
            <button
              onClick={handleSave}
              disabled={saving}
              className="ml-auto px-2.5 py-1 text-[9px] font-bold rounded-lg bg-brand-655 hover:bg-brand-600 text-white transition-all disabled:opacity-50"
            >
              {saving ? '...' : 'Save'}
            </button>
            <button
              onClick={() => { setEditing(false); const p = parseDuration(policy.duration_days); setVal(p.value); setUnit(p.unit) }}
              className="px-2 py-1 text-[9px] font-bold rounded-lg bg-slate-900 text-slate-450 hover:text-white"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between flex-1">
            <span className="text-[10px] text-slate-550 font-mono">
              After <span className="text-slate-300 font-bold">{val} {unit}</span>
            </span>
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1 text-[9px] font-bold text-brand-400 hover:text-brand-300"
            >
              <Edit3 className="w-3 h-3" /> Edit
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// --- ANIMATED FLOWCHART FLOW ---
function LifecycleFlowchart({ policies }) {
  const hotToWarm = policies.find(p => p.source_tier === 'hot' && p.dest_tier === 'warm')
  const warmToArchive = policies.find(p => p.source_tier === 'warm' && p.dest_tier === 'archive')
  
  const hotDays = hotToWarm ? hotToWarm.duration_days : 30
  const warmDays = warmToArchive ? warmToArchive.duration_days : 90
  const hotActive = hotToWarm ? hotToWarm.is_active : true
  const warmActive = warmToArchive ? warmToArchive.is_active : true

  const formatDurationLabel = (days) => {
    const totalMinutes = Math.round(days * 1440)
    if (totalMinutes === 0) return '0d'
    if (totalMinutes % 1440 === 0) return `${totalMinutes / 1440}d`
    if (totalMinutes % 60 === 0) return `${totalMinutes / 60}h`
    return `${totalMinutes}m`
  }

  return (
    <div className="p-4 bg-slate-950/60 border border-slate-900 rounded-2xl flex flex-col items-center gap-3.5 relative overflow-hidden select-none w-full">
      <div className="absolute top-0 right-0 w-16 h-16 bg-brand-500/5 rounded-full blur-xl pointer-events-none"></div>
      
      <div className="flex items-center w-full justify-between gap-1 text-[9px] font-bold">
        {/* Hot Tier */}
        <div className="flex flex-col items-center gap-1 px-2.5 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-xl shrink-0 shadow-inner">
          <span>🔥 Hot</span>
        </div>

        {/* Arrow 1 */}
        <div className="flex-1 flex flex-col items-center justify-center min-w-[30px]">
          <span className={`text-[8px] font-mono font-bold transition-colors ${hotActive ? 'text-amber-400' : 'text-slate-655'}`}>
            {formatDurationLabel(hotDays)}
          </span>
          <div className="flex items-center w-full gap-0.5 mt-0.5">
            <div className={`h-0.5 flex-1 rounded-full ${hotActive ? 'bg-amber-500/35' : 'bg-slate-800'}`}></div>
            <ArrowRight className={`w-2.5 h-2.5 shrink-0 ${hotActive ? 'text-amber-400 animate-arrowMove' : 'text-slate-700'}`} />
          </div>
        </div>

        {/* Warm Tier */}
        <div className="flex flex-col items-center gap-1 px-2.5 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl shrink-0 shadow-inner">
          <span>🌤 Warm</span>
        </div>

        {/* Arrow 2 */}
        <div className="flex-1 flex flex-col items-center justify-center min-w-[30px]">
          <span className={`text-[8px] font-mono font-bold transition-colors ${warmActive ? 'text-cyan-400' : 'text-slate-655'}`}>
            {formatDurationLabel(warmDays)}
          </span>
          <div className="flex items-center w-full gap-0.5 mt-0.5">
            <div className={`h-0.5 flex-1 rounded-full ${warmActive ? 'bg-cyan-500/35' : 'bg-slate-800'}`}></div>
            <ArrowRight className={`w-2.5 h-2.5 shrink-0 ${warmActive ? 'text-cyan-400 animate-arrowMove' : 'text-slate-700'}`} />
          </div>
        </div>

        {/* Archive Tier */}
        <div className="flex flex-col items-center gap-1 px-2.5 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-xl shrink-0 shadow-inner">
          <span>❄ Archive</span>
        </div>
      </div>
    </div>
  )
}

// --- VISUAL STORAGE JOURNEY TIMELINE ---
function StorageTimeline({ file }) {
  const isHot = file.current_tier === 'hot'
  const isWarm = file.current_tier === 'warm'
  const isArchive = file.current_tier === 'archive'
  
  const formatDate = (dateStr) => {
    if (!dateStr) return null
    return new Date(dateStr).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
  
  const uploadTime = formatDate(file.upload_date)
  const warmTime = (isWarm || isArchive) ? formatDate(file.next_migration_date || new Date(new Date(file.upload_date).getTime() + 30*24*60*60*1000)) : null
  const archiveTime = isArchive ? formatDate(new Date(new Date(file.upload_date).getTime() + 90*24*60*60*1000)) : null

  return (
    <div className="space-y-5 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800 pl-1 select-none">
      {/* Node 1: Hot Tier */}
      <div className="flex gap-3 relative">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border z-10 text-xs shadow-inner ${
          isHot ? 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse' : 'bg-slate-900 border-slate-850 text-slate-400'
        }`}>
          🔥
        </div>
        <div>
          <h4 className="text-[11px] font-bold text-slate-200">Stored in MinIO (Hot Storage)</h4>
          <p className="text-[9px] text-slate-500 mt-0.5">{uploadTime || 'Uploaded'}</p>
        </div>
      </div>

      {/* Node 2: Warm Tier */}
      <div className="flex gap-3 relative">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border z-10 text-xs shadow-inner ${
          isWarm ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400 animate-pulse' :
          isArchive ? 'bg-slate-900 border-slate-850 text-slate-400' : 'bg-slate-950 border-slate-900 text-slate-700'
        }`}>
          🌤
        </div>
        <div>
          <h4 className="text-[11px] font-bold text-slate-200">Migrated to SeaweedFS (Warm Storage)</h4>
          <p className="text-[9px] text-slate-550 mt-0.5">
            {isWarm || isArchive ? (warmTime || 'Completed') : 'Scheduled (After 30 days)'}
          </p>
        </div>
      </div>

      {/* Node 3: Archive Tier */}
      <div className="flex gap-3 relative">
        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border z-10 text-xs shadow-inner ${
          isArchive ? 'bg-purple-500/20 border-purple-500 text-purple-400 animate-pulse' : 'bg-slate-950 border-slate-900 text-slate-700'
        }`}>
          ❄
        </div>
        <div>
          <h4 className="text-[11px] font-bold text-slate-200">Archived to Scality S3 (Archive Storage)</h4>
          <p className="text-[9px] text-slate-550 mt-0.5">
            {isArchive ? (archiveTime || 'Completed') : 'Scheduled (After 90 days)'}
          </p>
        </div>
      </div>
    </div>
  )
}

// --- FILE CONSOLE INTERFACE ---
function Dashboard() {
  const { user, logout } = useAuth()
  
  // Custom Toast Notification System
  const [toasts, setToasts] = useState([])
  const addToast = (message, type = 'success') => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }

  // Google Drive-style + New Dropdown state
  const [showNewDropdown, setShowNewDropdown] = useState(false)

  // Floating Upload Queue state
  const [uploadQueue, setUploadQueue] = useState([]) 
  const [minimizeUploadQueue, setMinimizeUploadQueue] = useState(false)

  // Right-click Context Menu state
  const [contextMenu, setContextMenu] = useState({ x: 0, y: 0, visible: false, type: null, target: null })

  // Active File/Folder Details Drawer state
  const [activeDrawerFile, setActiveDrawerFile] = useState(null)

  // Active Admin Dashboard Tab state
  const [adminActiveTab, setAdminActiveTab] = useState('overview')

  // File Preview Modal states
  const [previewFile, setPreviewFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewContent, setPreviewContent] = useState('')

  // Navigation & Directory Tree States
  const [currentFolderId, setCurrentFolderId] = useState(null)
  const [breadcrumbs, setBreadcrumbs] = useState([]) // Array of { id, name }
  const [folders, setFolders] = useState([])
  const [files, setFiles] = useState([])
  const [loadingContents, setLoadingContents] = useState(true)

  // Creation & Edit Modals/Inputs
  const [showFolderModal, setShowFolderModal] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [renameTarget, setRenameTarget] = useState(null) // { type: 'file'|'folder', id, name }
  const [renameName, setRenameName] = useState('')

  // File Upload Status
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  // Service health checks state
  const [healthData, setHealthData] = useState(null)
  const [loadingHealth, setLoadingHealth] = useState(false)

  // Activity logs feed
  const [activities, setActivities] = useState([])
  const [loadingActivities, setLoadingActivities] = useState(false)

  // Admin Policy Triggers
  const [runningSweep, setRunningSweep] = useState(false)
  const [sweepResult, setSweepResult] = useState(null)

  // Admin Policy & Analytics States
  const [policies, setPolicies] = useState([])
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loadingPolicies, setLoadingPolicies] = useState(false)
  const [loadingAnalytics, setLoadingAnalytics] = useState(false)

  // Admin User Management
  const [users, setUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(false)

  // Admin Migration Queue
  const [migrations, setMigrations] = useState([])
  const [loadingMigrations, setLoadingMigrations] = useState(false)
  const [migrationFilter, setMigrationFilter] = useState('')

  // Search Filter
  const [searchQuery, setSearchQuery] = useState('')

  // 1. Fetch current directory items
  const fetchContents = async () => {
    setLoadingContents(true)
    try {
      const response = await axios.get('/folders/contents', {
        params: currentFolderId ? { parent_id: currentFolderId } : {}
      })
      setFolders(response.data.folders)
      setFiles(response.data.files)
      // Automatically refresh analytics on content changes
      fetchAnalytics()
    } catch (err) {
      console.error('Failed to load files and folders:', err)
    } finally {
      setLoadingContents(false)
    }
  }

  // 1b. Fetch Policies
  const fetchPolicies = async () => {
    if (user?.role !== 'admin') return
    setLoadingPolicies(true)
    try {
      const response = await axios.get('/admin/lifecycle/policies')
      setPolicies(response.data)
    } catch (err) {
      console.error('Failed to fetch lifecycle policies:', err)
    } finally {
      setLoadingPolicies(false)
    }
  }

  // 1c. Fetch Analytics
  const fetchAnalytics = async () => {
    if (user?.role !== 'admin') return
    setLoadingAnalytics(true)
    try {
      const response = await axios.get('/admin/analytics')
      setAnalyticsData(response.data)
    } catch (err) {
      console.error('Failed to fetch storage analytics:', err)
    } finally {
      setLoadingAnalytics(false)
    }
  }

  // 2. Fetch Storage Infrastructure Health
  const fetchHealth = async () => {
    setLoadingHealth(true)
    try {
      const response = await axios.get('/health')
      setHealthData(response.data)
    } catch (err) {
      if (err.response?.data?.detail?.services) {
        setHealthData(err.response.data.detail)
      }
    } finally {
      setLoadingHealth(false)
    }
  }

  // 4. Fetch All Users (admin)
  const fetchUsers = async () => {
    if (user?.role !== 'admin') return
    setLoadingUsers(true)
    try {
      const response = await axios.get('/admin/users')
      setUsers(response.data)
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoadingUsers(false)
    }
  }

  // 5. Fetch Migration Queue (admin)
  const fetchMigrations = async () => {
    if (user?.role !== 'admin') return
    setLoadingMigrations(true)
    try {
      const params = migrationFilter ? { status: migrationFilter } : {}
      const response = await axios.get('/admin/migrations', { params })
      setMigrations(response.data)
    } catch (err) {
      console.error('Failed to fetch migrations:', err)
    } finally {
      setLoadingMigrations(false)
    }
  }

  // 3. Fetch Activity Log History (all users for admin)
  const fetchActivities = async () => {
    setLoadingActivities(true)
    try {
      const endpoint = user?.role === 'admin' ? '/admin/activities' : '/activities'
      const response = await axios.get(endpoint)
      setActivities(response.data)
    } catch (err) {
      console.error('Failed to load activity logs:', err)
    } finally {
      setLoadingActivities(false)
    }
  }

  // Effect triggers on directory changes
  useEffect(() => {
    fetchContents()
  }, [currentFolderId])

  // Initial dashboard load
  useEffect(() => {
    fetchHealth()
    fetchActivities()
    fetchPolicies()
    fetchAnalytics()
    fetchUsers()
    fetchMigrations()
  }, [])

  // Navigation handlers
  const handleFolderClick = (folder) => {
    setBreadcrumbs(prev => [...prev, { id: folder.id, name: folder.name }])
    setCurrentFolderId(folder.id)
  }

  const handleBreadcrumbClick = (index) => {
    if (index === -1) {
      setBreadcrumbs([])
      setCurrentFolderId(null)
    } else {
      const target = breadcrumbs[index]
      setBreadcrumbs(prev => prev.slice(0, index + 1))
      setCurrentFolderId(target.id)
    }
  }

  // Format File Size
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Rich File Icon Mapper
  const getFileIcon = (file) => {
    const ext = file.extension?.toLowerCase()
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
      return <Image className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['mp4', 'mkv', 'avi', 'mov', 'webm'].includes(ext)) {
      return <Video className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-red-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['doc', 'docx'].includes(ext)) {
      return <FileText className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['xls', 'xlsx'].includes(ext)) {
      return <FileSpreadsheet className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
      return <FileArchive className="w-5 h-5 text-amber-500 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext)) {
      return <FileAudio className="w-5 h-5 text-violet-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['md', 'markdown'].includes(ext)) {
      return <FileText className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['txt', 'log'].includes(ext)) {
      return <FileText className="w-5 h-5 text-slate-400 group-hover:scale-110 transition-transform duration-200" />
    }
    if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'html', 'css', 'json', 'yaml', 'yml', 'go', 'sh', 'bat'].includes(ext)) {
      return <FileCode className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform duration-200" />
    }
    return <File className="w-5 h-5 text-slate-450 group-hover:scale-110 transition-transform duration-200" />
  }  // --- CONTROLLER ACTIONS ---

  // Create folder
  const handleCreateFolder = async (e) => {
    if (e && e.preventDefault) e.preventDefault()
    if (!newFolderName.trim()) return
    try {
      await axios.post('/folders', {
        name: newFolderName,
        parent_id: currentFolderId
      })
      addToast(`Folder "${newFolderName}" created successfully`, 'success')
      setNewFolderName('')
      setShowFolderModal(false)
      fetchContents()
      fetchActivities()
    } catch (err) {
      addToast('Failed to create folder', 'error')
    }
  }

  // Upload File (Axios with real upload progress tracking)
  const handleFileUpload = async (e, folderOverrideId = null) => {
    const filesToUpload = e.target.files
    if (!filesToUpload || filesToUpload.length === 0) return

    const targetFolderId = folderOverrideId || currentFolderId

    for (let i = 0; i < filesToUpload.length; i++) {
      const uploadedFile = filesToUpload[i]
      const queueId = Date.now() + Math.random()
      const source = axios.CancelToken.source()

      // Add to queue
      setUploadQueue(prev => [
        {
          id: queueId,
          name: uploadedFile.name,
          progress: 0,
          speed: '0 B/s',
          remainingTime: 'Calculating...',
          status: 'uploading',
          cancelTokenSource: source,
          fileObject: uploadedFile
        },
        ...prev
      ])

      const formData = new FormData()
      formData.append('file', uploadedFile)
      if (targetFolderId) {
        formData.append('folder_id', targetFolderId)
      }

      let startTime = Date.now()

      axios.post('/files/upload', formData, {
        cancelToken: source.token,
        onUploadProgress: (progressEvent) => {
          const loaded = progressEvent.loaded
          const total = progressEvent.total
          const progress = Math.round((loaded * 100) / total)
          
          const elapsedSeconds = (Date.now() - startTime) / 1000
          const speedBytes = elapsedSeconds > 0 ? loaded / elapsedSeconds : 0
          const speed = speedBytes > 1048576 
            ? (speedBytes / 1048576).toFixed(1) + ' MB/s' 
            : speedBytes > 1024 
              ? (speedBytes / 1024).toFixed(0) + ' KB/s' 
              : speedBytes.toFixed(0) + ' B/s'
          
          const remainingBytes = total - loaded
          let remainingTime = 'Calculating...'
          if (speedBytes > 0) {
            const remSec = remainingBytes / speedBytes
            if (remSec > 60) {
              remainingTime = Math.floor(remSec / 60) + 'm ' + Math.floor(remSec % 60) + 's'
            } else {
              remainingTime = Math.floor(remSec) + 's'
            }
          }

          setUploadQueue(prev => prev.map(item => {
            if (item.id === queueId && item.status === 'uploading') {
              return { ...item, progress, speed, remainingTime }
            }
            return item
          }))
        }
      }).then(() => {
        addToast(`Uploaded "${uploadedFile.name}" successfully`, 'success')
        setUploadQueue(prev => prev.map(item => {
          if (item.id === queueId) {
            return { ...item, progress: 100, status: 'completed', speed: 'Done', remainingTime: '0s' }
          }
          return item
        }))
        fetchContents()
        fetchActivities()
      }).catch(err => {
        if (axios.isCancel(err)) {
          addToast(`Upload of "${uploadedFile.name}" cancelled`, 'info')
          setUploadQueue(prev => prev.map(item => {
            if (item.id === queueId) {
              return { ...item, status: 'cancelled', speed: '--', remainingTime: '--' }
            }
            return item
          }))
        } else {
          addToast(`Upload failed: ${uploadedFile.name}`, 'error')
          setUploadQueue(prev => prev.map(item => {
            if (item.id === queueId) {
              return { ...item, status: 'failed', speed: '--', remainingTime: '--' }
            }
            return item
          }))
        }
      })
    }
  }

  // Download File Stream
  const handleDownloadFile = async (file) => {
    addToast(`Downloading "${file.name}"...`, 'info')
    try {
      const response = await axios.get(`/files/download/${file.id}`, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: response.headers['content-type'] })
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = file.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(link.href)
      addToast(`Downloaded "${file.name}" successfully`, 'success')
      fetchActivities()
    } catch (err) {
      addToast(`Failed to download "${file.name}"`, 'error')
    }
  }
  // File Preview Handlers
  const handlePreviewFile = async (file) => {
    setPreviewFile(file)
    setPreviewLoading(true)
    setPreviewUrl('')
    setPreviewContent('')
    try {
      const response = await axios.get(`/files/download/${file.id}`, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: response.headers['content-type'] })
      const url = window.URL.createObjectURL(blob)
      setPreviewUrl(url)

      const ext = file.extension?.toLowerCase()
      if (['txt', 'md', 'json', 'js', 'py', 'html', 'css', 'xml', 'ini', 'cfg', 'conf'].includes(ext)) {
        const text = await blob.text()
        setPreviewContent(text)
      }
    } catch (err) {
      addToast('Failed to load file preview', 'error')
      setPreviewFile(null)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleClosePreview = () => {
    if (previewUrl) window.URL.revokeObjectURL(previewUrl)
    setPreviewFile(null)
    setPreviewUrl('')
    setPreviewContent('')
  }
  // Rename File/Folder
  const handleRenameSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault()
    if (!renameName.trim()) return
    try {
      if (renameTarget.type === 'folder') {
        await axios.patch(`/folders/${renameTarget.id}`, { name: renameName })
      } else {
        await axios.patch(`/files/${renameTarget.id}`, { name: renameName })
      }
      addToast('Rename successful', 'success')
      setRenameTarget(null)
      setRenameName('')
      fetchContents()
      fetchActivities()
    } catch (err) {
      addToast('Failed to rename', 'error')
    }
  }

  // Delete Folder
  const handleDeleteFolder = async (folder) => {
    if (!confirm(`Are you sure you want to delete folder "${folder.name}"? This will recursively delete all nested folders and files inside it!`)) return
    try {
      await axios.delete(`/folders/${folder.id}`)
      addToast(`Folder "${folder.name}" deleted successfully`, 'success')
      fetchContents()
      fetchActivities()
    } catch (err) {
      addToast('Failed to delete folder.', 'error')
    }
  }

  // Delete File
  const handleDeleteFile = async (file) => {
    if (!confirm(`Are you sure you want to delete file "${file.name}"?`)) return
    try {
      await axios.delete(`/files/${file.id}`)
      addToast(`File "${file.name}" deleted successfully`, 'success')
      fetchContents()
      fetchActivities()
      if (activeDrawerFile?.id === file.id) {
        setActiveDrawerFile(null)
      }
    } catch (err) {
      addToast('Failed to delete file.', 'error')
    }
  }

  // Admin Policy Sweep Trigger
  const handleTriggerSweep = async () => {
    setRunningSweep(true)
    setSweepResult(null)
    addToast('Triggering lifecycle policy sweep...', 'info')
    try {
      const response = await axios.post('/admin/lifecycle/trigger')
      setSweepResult({
        success: true,
        message: response.data.message,
        triggered: response.data.migrations_triggered
      })
      if (response.data.migrations_triggered > 0) {
        addToast(`Sweep complete! Triggered ${response.data.migrations_triggered} migration(s).`, 'success')
      } else {
        addToast('Sweep complete. No files qualified for migration.', 'success')
      }
      fetchContents()
      fetchActivities()
    } catch (err) {
      setSweepResult({
        success: false,
        message: err.response?.data?.detail || 'Sweep execution failed.'
      })
      addToast('Sweep execution failed.', 'error')
    } finally {
      setRunningSweep(false)
    }
  }

  // Admin Policy Update Action
  const handleUpdatePolicy = async (id, duration, isActive) => {
    try {
      await axios.patch(`/admin/lifecycle/policies/${id}`, {
        duration_days: parseFloat(duration),
        is_active: isActive
      })
      fetchPolicies()
      fetchActivities()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update policy.')
    }
  }

  // Admin User Management Actions
  const handleToggleUserActive = async (userId, currentActive) => {
    try {
      await axios.patch(`/admin/users/${userId}`, { is_active: !currentActive })
      fetchUsers()
      fetchActivities()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update user')
    }
  }

  const handleToggleUserRole = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin'
    try {
      await axios.patch(`/admin/users/${userId}`, { role: newRole })
      fetchUsers()
      fetchActivities()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update user role')
    }
  }

  // Rendering Helper
  const getServiceStatus = (serviceName) => {
    if (!healthData || !healthData.services) return 'checking'
    return healthData.services[serviceName] || 'offline'
  }

  const renderStatusBadge = (status) => {
    if (status.startsWith('online')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Online
        </span>
      )
    } else if (status === 'checking') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Verifying
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Offline
        </span>
      )
    }
  }

  // Close dropdowns and context menus on outside click
  useEffect(() => {
    const handleGlobalClick = () => {
      setShowNewDropdown(false)
      setContextMenu(prev => prev.visible ? { ...prev, visible: false } : prev)
    }
    document.addEventListener('click', handleGlobalClick)
    return () => document.removeEventListener('click', handleGlobalClick)
  }, [])

  // Advanced Search Query Parser supporting filters: type, storage, tier
  const parseSearchQuery = (query) => {
    let text = ''
    let type = null
    let storage = null
    let tier = null

    const tokens = query.split(/\s+/)
    tokens.forEach(token => {
      if (token.startsWith('type:')) {
        type = token.substring(5).toLowerCase()
      } else if (token.startsWith('storage:')) {
        storage = token.substring(8).toLowerCase()
      } else if (token.startsWith('tier:')) {
        tier = token.substring(5).toLowerCase()
      } else if (token) {
        text += (text ? ' ' : '') + token.toLowerCase()
      }
    })

    return { text, type, storage, tier }
  }

  // Filtering search matches
  const { text: searchTxt, type: searchType, storage: searchStorage, tier: searchTier } = parseSearchQuery(searchQuery)

  const filteredFolders = folders.filter(f => {
    // Folders only match text search
    if (searchType || searchStorage || searchTier) return false
    return f.name.toLowerCase().includes(searchTxt)
  })

  const filteredFiles = files.filter(f => {
    if (searchTxt && !f.name.toLowerCase().includes(searchTxt)) return false
    if (searchType && f.extension?.toLowerCase() !== searchType) return false
    
    // Storage backend check (minio, seaweedfs, scality)
    if (searchStorage) {
      const backend = (f.current_backend || '').toLowerCase()
      if (!backend.includes(searchStorage)) return false
    }
    
    // Lifecycle tier check (hot, warm, archive)
    if (searchTier && (f.current_tier || '').toLowerCase() !== searchTier) return false
    
    return true
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-[-30%] left-[-30%] w-[70%] h-[70%] rounded-full bg-brand-500/5 blur-[180px] pointer-events-none"></div>
      <div className="absolute bottom-[-30%] right-[-30%] w-[70%] h-[70%] rounded-full bg-indigo-500/5 blur-[180px] pointer-events-none"></div>

      {/* Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-brand-600 p-2 rounded-lg text-white shadow-lg shadow-brand-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-outfit text-base font-bold tracking-tight text-white">
                CloudVault
              </h1>
              <p className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Multi-Tier storage dashboard</p>
            </div>
          </div>

          {/* Search bar */}
          <div className="hidden sm:flex items-center relative max-w-xs w-full">
            <Search className="w-4 h-4 text-slate-500 absolute left-3" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 bg-slate-900 border border-slate-850 rounded-xl text-slate-200 placeholder-slate-650 text-xs focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>

          {/* User Console info */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="flex flex-col text-right">
                <span className="text-xs font-bold text-slate-200">{user?.full_name}</span>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1 justify-end">
                  {user?.role === 'admin' ? (
                    <>
                      <Shield className="w-2.5 h-2.5 text-brand-400" />
                      Administrator
                    </>
                  ) : (
                    <>
                      <UserIcon className="w-2.5 h-2.5 text-slate-500" />
                      User
                    </>
                  )}
                </span>
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-rose-400 border border-transparent hover:border-slate-850 transition-all duration-150"
                title="Sign Out"
              >
                <LogOut className="w-4.5 h-4.5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row gap-6 relative z-10">
        
        {/* Left Side: File Explorer */}
        <div className="flex-1 bg-slate-900/30 border border-slate-900 rounded-3xl p-6 backdrop-blur-sm flex flex-col min-h-[500px]">
          
          {/* Breadcrumbs and Actions Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-900 pb-5 mb-5">
            {/* Breadcrumb Path */}
            <div className="flex items-center text-xs font-bold select-none">
              <button
                onClick={() => handleBreadcrumbClick(-1)}
                className="flex items-center gap-1.5 text-slate-450 hover:text-white transition-colors"
              >
                <Home className="w-3.5 h-3.5" />
                <span>Root</span>
              </button>
              
              {breadcrumbs.map((folder, index) => (
                <React.Fragment key={folder.id}>
                  <span className="text-slate-700 mx-2 font-light">&gt;</span>
                  <button
                    onClick={() => handleBreadcrumbClick(index)}
                    className="text-slate-400 hover:text-white transition-colors truncate max-w-[120px]"
                  >
                    {folder.name}
                  </button>
                </React.Fragment>
              ))}
            </div>

            {/* Google Drive-style + New Dropdown */}
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowNewDropdown(!showNewDropdown)
                }}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-brand-655 hover:bg-brand-600 text-white transition-all shadow-md shadow-brand-655/15"
              >
                <Plus className="w-4 h-4" />
                <span>New</span>
                <ChevronDown className="w-3.5 h-3.5" />
              </button>

              {showNewDropdown && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-850 rounded-2xl shadow-2xl py-1.5 z-50 animate-scaleIn">
                  <button
                    onClick={() => {
                      setShowNewDropdown(false)
                      setShowFolderModal(true)
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-850/30 flex items-center gap-2 transition-colors"
                  >
                    <FolderPlus className="w-4 h-4 text-brand-400" />
                    <span>Create Folder</span>
                  </button>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation()
                      document.getElementById('file-upload-input').click()
                      setTimeout(() => setShowNewDropdown(false), 100)
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-850/30 flex items-center gap-2 transition-colors"
                  >
                    <Upload className="w-4 h-4 text-emerald-400" />
                    <span>Upload File</span>
                  </button>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation()
                      document.getElementById('folder-upload-input').click()
                      setTimeout(() => setShowNewDropdown(false), 100)
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-850/30 flex items-center gap-2 transition-colors"
                  >
                    <FolderOpen className="w-4 h-4 text-sky-400" />
                    <span>Upload Folder</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Upload Error Banner */}
          {uploadError && (
            <div className="mb-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-450 text-xs flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {uploadError}
              </span>
              <button onClick={() => setUploadError(null)} className="p-1 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Directory Contents Grid */}
          <div className="flex-1 flex flex-col justify-between">
            {loadingContents ? (
              <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500 gap-3">
                <RefreshCw className="w-8 h-8 animate-spin text-brand-500" />
                <span className="text-xs font-semibold">Loading contents...</span>
              </div>
            ) : filteredFolders.length === 0 && filteredFiles.length === 0 ? (
              searchQuery ? (
                /* No Search Results State */
                <div className="flex-1 flex flex-col items-center justify-center py-16 text-slate-500 gap-4 animate-fadeIn">
                  <div className="bg-slate-900/50 p-5 rounded-3xl border border-slate-850/60 shadow-lg">
                    <Search className="w-10 h-10 text-slate-450" />
                  </div>
                  <div className="text-center max-w-sm">
                    <p className="text-sm font-bold text-slate-200">No search results found</p>
                    <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                      We couldn't find anything matching "<span className="text-slate-350 font-bold">{searchQuery}</span>". 
                      Try using search filters like <span className="font-mono text-brand-400">type:pdf</span> or <span className="font-mono text-brand-400">tier:archive</span>.
                    </p>
                  </div>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="px-4 py-2 text-xs font-bold rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-300 border border-slate-850 transition-colors"
                  >
                    Clear Search
                  </button>
                </div>
              ) : (
                /* Empty Folder State */
                <div className="flex-1 flex flex-col items-center justify-center py-16 text-slate-500 gap-4 animate-fadeIn">
                  <div className="bg-slate-900/50 p-5 rounded-3xl border border-slate-850/60 shadow-lg relative group">
                    <div className="absolute inset-0 bg-brand-500/5 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <Folder className="w-10 h-10 text-slate-400 group-hover:scale-110 transition-transform duration-300 relative z-10" />
                  </div>
                  <div className="text-center max-w-sm">
                    <p className="text-sm font-bold text-slate-200">This folder is empty</p>
                    <p className="text-xs text-slate-550 mt-1.5 leading-relaxed">
                      Upload your files or create a new directory using the "+ New" button to get started.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowFolderModal(true)}
                    className="px-4 py-2 text-xs font-bold rounded-xl bg-slate-900 hover:bg-slate-850 text-brand-400 border border-slate-850 transition-colors"
                  >
                    Create Folder
                  </button>
                </div>
              )
            ) : (
              <div className="space-y-6">
                {/* Folders Section */}
                {filteredFolders.length > 0 && (
                  <div>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Folders</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {filteredFolders.map(folder => (
                        <div
                          key={folder.id}
                          onContextMenu={(e) => handleContextMenu(e, 'folder', folder)}
                          onClick={() => handleFolderClick(folder)}
                          className="group relative p-3.5 bg-slate-950/40 border border-slate-900 hover:border-slate-800 hover:scale-[1.01] hover:shadow-lg rounded-2xl flex items-center justify-between hover:bg-slate-900/20 transition-all duration-200 cursor-pointer"
                        >
                          <div className="flex items-center gap-3 min-w-0 flex-1 pr-8">
                            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400 group-hover:bg-brand-500 group-hover:text-white transition-all shadow-inner">
                              <Folder className="w-4.5 h-4.5" />
                            </div>
                            <span className="text-xs font-bold text-slate-200 group-hover:text-white truncate">
                              {folder.name}
                            </span>
                          </div>

                          {/* Hover Action Menu */}
                          <button
                            onClick={(e) => handleThreeDotClick(e, 'folder', folder)}
                            className="p-1 hover:bg-slate-800 text-slate-450 hover:text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                            title="More Actions"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Files Section */}
                {filteredFiles.length > 0 && (
                  <div>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Files</h3>
                    <div className="space-y-2">
                      {filteredFiles.map(file => (
                        <div
                          key={file.id}
                          onContextMenu={(e) => handleContextMenu(e, 'file', file)}
                          onClick={() => setActiveDrawerFile(file)}
                          className="group p-3 bg-slate-950/40 border border-slate-900 hover:border-slate-800 hover:scale-[1.005] hover:shadow-lg rounded-2xl flex items-center justify-between hover:bg-slate-900/20 transition-all duration-200 cursor-pointer"
                        >
                          <div className="flex items-center gap-3 min-w-0 flex-1 pr-6">
                            <div className="p-2 rounded-xl bg-slate-900 border border-slate-850 shadow-inner shrink-0">
                              {getFileIcon(file)}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-xs font-bold text-slate-200 group-hover:text-white truncate">
                                {file.name}
                              </p>
                              <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                                <span>{formatBytes(file.size)}</span>
                                <span>&bull;</span>
                                <span className="lowercase">{file.extension || 'file'}</span>
                                <span>&bull;</span>
                                <span className="capitalize">{file.current_backend || 'MinIO'}</span>
                              </div>
                            </div>
                          </div>

                          {/* Badges & Actions */}
                          <div className="flex items-center gap-3 shrink-0">
                            {/* Tier Badge */}
                            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border bg-slate-950/60 uppercase tracking-wider ${
                              file.current_tier === 'hot' ? 'text-amber-400 border-amber-500/20 bg-amber-500/5' :
                              file.current_tier === 'warm' ? 'text-cyan-400 border-cyan-500/20 bg-cyan-500/5' :
                              'text-purple-400 border-purple-500/20 bg-purple-500/5'
                            }`}>
                              {file.current_tier === 'hot' ? '🔥 Hot' :
                               file.current_tier === 'warm' ? '🌤 Warm' :
                               '❄ Archive'}
                            </span>
                            
                            {/* Hover Action Menu */}
                            <button
                              onClick={(e) => handleThreeDotClick(e, 'file', file)}
                              className="p-1 hover:bg-slate-800 text-slate-450 hover:text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                              title="More Actions"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
              )}
            </div>
          )
        }
      </div>
    </div>
               {/* Right Side Pane: Console Audits & Services */}
        <div className="w-full md:w-80 flex flex-col gap-6 shrink-0">
          
          {/* Tabbed Admin Dashboard Card */}
          {user?.role === 'admin' && (
            <div className="bg-slate-900/40 border border-slate-900 rounded-3xl p-5 backdrop-blur-sm relative overflow-hidden flex flex-col min-h-[380px] shadow-lg">
              <div className="absolute top-0 right-0 w-20 h-20 bg-brand-500/5 rounded-full blur-xl pointer-events-none"></div>
              
              <div className="flex items-center justify-between mb-4 shrink-0 select-none">
                <h3 className="font-outfit text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-4 h-4 text-brand-400" /> Admin Console
                </h3>
              </div>

              {/* Tabs Navigation */}
              <div className="flex gap-1.5 border-b border-slate-850 pb-2 mb-3.5 overflow-x-auto shrink-0 scrollbar-thin select-none">
                {[
                  { id: 'overview', label: 'Overview' },
                  { id: 'users', label: 'Users' },
                  { id: 'storage', label: 'Storage' },
                  { id: 'queue', label: 'Queue' },
                  { id: 'policies', label: 'Policies' },
                  { id: 'logs', label: 'Logs' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setAdminActiveTab(tab.id)}
                    className={`px-2.5 py-1 text-[10px] font-bold rounded-lg border transition-all shrink-0 ${
                      adminActiveTab === tab.id
                        ? 'bg-brand-655 text-white border-brand-500 shadow-sm'
                        : 'bg-slate-950 text-slate-450 border-slate-900 hover:text-white'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Contents */}
              <div className="flex-1 overflow-y-auto min-h-0 pr-1 scrollbar-thin">
                
                {/* 1. OVERVIEW TAB */}
                {adminActiveTab === 'overview' && (
                  <div className="space-y-4 animate-fadeIn">
                    <LifecycleFlowchart policies={policies} />
                    
                    <div className="border-t border-slate-900 pt-3">
                      <h4 className="font-outfit text-xs font-bold text-white flex items-center gap-2 mb-2">
                        <Activity className="w-3.5 h-3.5 text-brand-400" /> Manual Sweep
                      </h4>
                      <p className="text-[10px] text-slate-500 mb-3 leading-relaxed">
                        Trigger a lifecycle sweep to evaluate policies and migrate matching files immediately.
                      </p>
                      
                      {sweepResult && (
                        <div className={`mb-3 p-3 rounded-xl border text-[10px] leading-relaxed ${
                          sweepResult.success
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                            : 'bg-rose-500/10 border-rose-500/20 text-rose-450'
                        }`}>
                          <p className="font-bold">{sweepResult.message}</p>
                          {sweepResult.triggered !== undefined && (
                            <p className="mt-1 font-mono text-[9px] text-slate-400">
                              Migrations triggered: {sweepResult.triggered}
                            </p>
                          )}
                        </div>
                      )}

                      <button
                        onClick={handleTriggerSweep}
                        disabled={runningSweep}
                        className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-xl bg-slate-950 hover:bg-slate-900 text-brand-400 hover:text-brand-300 border border-slate-850 active:scale-98 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${runningSweep ? 'animate-spin' : ''}`} />
                        {runningSweep ? 'Running...' : 'Run Sweep Now'}
                      </button>
                    </div>
                  </div>
                )}

                {/* 2. USERS TAB */}
                {adminActiveTab === 'users' && (
                  <div className="space-y-2.5 animate-fadeIn">
                    <div className="flex items-center justify-between shrink-0 mb-1 select-none">
                      <span className="text-[9px] text-slate-550 uppercase font-bold tracking-wider">User Directory</span>
                      <button onClick={fetchUsers} disabled={loadingUsers} className="text-[9px] text-brand-400 hover:underline">Refresh</button>
                    </div>
                    {loadingUsers ? (
                      <div className="text-center py-6 text-[10px] font-semibold text-slate-650">Loading users...</div>
                    ) : users.length === 0 ? (
                      <div className="text-center py-6 text-[10px] font-semibold text-slate-600">No users found</div>
                    ) : (
                      users.map(u => (
                        <div key={u.id} className="p-3 rounded-xl bg-slate-950/40 border border-slate-900 text-[10px] hover:border-slate-850 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="min-w-0 flex-1 pr-2">
                              <p className="font-bold text-slate-200 truncate">{u.full_name || u.email}</p>
                              <p className="text-slate-550 truncate mt-0.5">{u.email}</p>
                            </div>
                            <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase shrink-0 ${
                              u.role === 'admin'
                                ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                                : 'bg-slate-800 text-slate-450 border border-slate-800'
                            }`}>
                              {u.role}
                            </span>
                          </div>
                          <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-900/60">
                            <button
                              onClick={() => handleToggleUserActive(u.id, u.is_active)}
                              className={`flex items-center gap-1 text-[9px] font-bold hover:text-white ${
                                u.is_active ? 'text-emerald-400' : 'text-rose-450'
                              }`}
                            >
                              {u.is_active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                              {u.is_active ? 'Active' : 'Disabled'}
                            </button>
                            <button
                              onClick={() => handleToggleUserRole(u.id, u.role)}
                              className="text-[9px] font-bold text-slate-500 hover:text-brand-400 flex items-center gap-1"
                            >
                              <Shield className="w-3 h-3" />
                              Toggle Role
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* 3. STORAGE TAB */}
                {adminActiveTab === 'storage' && (
                  <div className="space-y-4 animate-fadeIn">
                    <div className="flex items-center justify-between select-none">
                      <span className="text-[9px] text-slate-550 uppercase font-bold tracking-wider">Metrics</span>
                      <button onClick={fetchAnalytics} disabled={loadingAnalytics} className="text-[9px] text-brand-400 hover:underline">Refresh</button>
                    </div>

                    {analyticsData ? (() => {
                      const totalBytes = analyticsData.total_size_bytes || 1
                      const tiers = [
                        { key: 'hot', label: 'MinIO (Hot)', color: 'bg-amber-500', textColor: 'text-amber-450', borderColor: 'border-amber-500/20' },
                        { key: 'warm', label: 'SeaweedFS (Warm)', color: 'bg-cyan-500', textColor: 'text-cyan-450', borderColor: 'border-cyan-500/20' },
                        { key: 'archive', label: 'Scality (Archive)', color: 'bg-purple-500', textColor: 'text-purple-455', borderColor: 'border-purple-500/20' }
                      ]
                      return (
                        <div className="space-y-3.5">
                          {tiers.map(tier => {
                            const data = analyticsData.tiers[tier.key]
                            const pct = totalBytes > 0 ? Math.round((data.total_size_bytes / totalBytes) * 100) : 0
                            return (
                              <div key={tier.key}>
                                <div className="flex items-center justify-between mb-1.5">
                                  <span className="text-[10px] font-bold text-slate-350 flex items-center gap-1">
                                    <span className={`w-1.5 h-1.5 rounded-full ${tier.color}`}></span>
                                    {tier.label}
                                  </span>
                                  <span className="text-[9px] font-mono text-slate-500">
                                    {data.file_count} files &bull; {formatBytes(data.total_size_bytes)}
                                  </span>
                                </div>
                                <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-900">
                                  <div
                                    className={`h-full ${tier.color} transition-all duration-700`}
                                    style={{ width: `${pct}%`, minWidth: data.file_count > 0 ? '4px' : '0px' }}
                                  ></div>
                                </div>
                              </div>
                            )
                          })}
                          <div className="mt-4 pt-3.5 border-t border-slate-900 flex justify-between items-center text-[10px] font-bold">
                            <span className="text-slate-500 flex items-center gap-1">Total Capacity</span>
                            <span className="text-slate-300">
                              {analyticsData.total_files} files ({formatBytes(analyticsData.total_size_bytes)})
                            </span>
                          </div>
                        </div>
                      )
                    })() : (
                      <div className="text-center py-6 text-[10px] font-semibold text-slate-600">
                        {loadingAnalytics ? 'Loading analytics...' : 'No metrics loaded.'}
                      </div>
                    )}
                  </div>
                )}

                {/* 4. MIGRATION QUEUE TAB */}
                {adminActiveTab === 'queue' && (
                  <div className="space-y-3 animate-fadeIn">
                    <div className="flex items-center justify-between select-none">
                      <span className="text-[9px] text-slate-550 uppercase font-bold tracking-wider">Celery Queue</span>
                      <button onClick={fetchMigrations} disabled={loadingMigrations} className="text-[9px] text-brand-400 hover:underline">Refresh</button>
                    </div>

                    <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-thin select-none">
                      {['', 'in_progress', 'success', 'failed'].map(s => (
                        <button
                          key={s}
                          onClick={() => setMigrationFilter(s)}
                          className={`px-2 py-0.5 text-[8px] font-bold rounded border transition-all ${
                            migrationFilter === s
                              ? 'bg-brand-655 text-white border-brand-500'
                              : 'bg-slate-950 text-slate-450 border-slate-900 hover:text-white'
                          }`}
                        >
                          {s || 'All'}
                        </button>
                      ))}
                    </div>

                    <div className="space-y-2 max-h-[220px] overflow-y-auto pr-0.5 scrollbar-thin">
                      {loadingMigrations ? (
                        <div className="text-center py-6 text-[10px] font-semibold text-slate-650">Loading migrations...</div>
                      ) : migrations.length === 0 ? (
                        <div className="text-center py-6 text-[10px] font-semibold text-slate-600">No migrations found</div>
                      ) : (
                        migrations.map(m => (
                          <div key={m.id} className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-900 text-[10px]">
                            <div className="flex items-center justify-between font-bold">
                              <span>File #{m.file_id}</span>
                              <span className={`text-[8px] px-1 py-0.5 rounded capitalize ${
                                m.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                m.status === 'failed' ? 'bg-rose-500/10 text-rose-455 border border-rose-500/20' :
                                'bg-amber-500/10 text-amber-450 border border-amber-500/20'
                              }`}>
                                {m.status === 'in_progress' ? 'Running' : m.status}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-1.5 text-slate-500 font-semibold">
                              <span className="capitalize">{m.source_tier}</span>
                              <span>➔</span>
                              <span className="capitalize">{m.dest_tier}</span>
                            </div>
                            {m.error_message && (
                              <p className="mt-1 text-rose-400 text-[9px] truncate" title={m.error_message}>{m.error_message}</p>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* 5. POLICIES TAB */}
                {adminActiveTab === 'policies' && (
                  <div className="space-y-3 animate-fadeIn">
                    <div className="flex items-center justify-between select-none">
                      <span className="text-[9px] text-slate-550 uppercase font-bold tracking-wider">Policy Engine</span>
                      <button onClick={fetchPolicies} disabled={loadingPolicies} className="text-[9px] text-brand-400 hover:underline">Refresh</button>
                    </div>

                    {loadingPolicies ? (
                      <div className="text-center py-6 text-[10px] font-semibold text-slate-650">Loading policies...</div>
                    ) : policies.length === 0 ? (
                      <div className="text-center py-6 text-[10px] font-semibold text-slate-600">No policies found</div>
                    ) : (
                      <div className="space-y-3">
                        {policies.map(policy => (
                          <PolicyRow
                            key={policy.id}
                            policy={policy}
                            onUpdate={handleUpdatePolicy}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 6. LOGS TAB */}
                {adminActiveTab === 'logs' && (
                  <div className="space-y-2.5 animate-fadeIn">
                    <div className="flex items-center justify-between select-none">
                      <span className="text-[9px] text-slate-550 uppercase font-bold tracking-wider">Audit Log Feed</span>
                      <button onClick={fetchActivities} disabled={loadingActivities} className="text-[9px] text-brand-400 hover:underline">Refresh</button>
                    </div>

                    <div className="space-y-2 max-h-[220px] overflow-y-auto pr-0.5 scrollbar-thin">
                      {loadingActivities ? (
                        <div className="text-center py-6 text-[10px] font-semibold text-slate-650">Loading audit feed...</div>
                      ) : activities.length === 0 ? (
                        <div className="text-center py-6 text-[10px] font-semibold text-slate-600">No logs found</div>
                      ) : (
                        activities.map(log => (
                          <div key={log.id} className="p-2 bg-slate-950/40 border border-slate-900 rounded-xl text-[9px] leading-relaxed">
                            <div className="flex items-center justify-between font-bold text-slate-350">
                              <span className="capitalize">{log.action.replace('_', ' ')}</span>
                              <span className="text-slate-600 font-medium">
                                {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <p className="text-slate-450 mt-0.5">{log.details}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

              </div>
            </div>
          )}

          {/* Infrastructure Health Card */}
          <div className="bg-slate-900/40 border border-slate-900 rounded-3xl p-5 backdrop-blur-sm shadow-md">
            <div className="flex items-center justify-between border-b border-slate-850 pb-3 mb-3 shrink-0 select-none">
              <h3 className="font-outfit text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-brand-400" /> Infrastructure
              </h3>
              <button
                onClick={fetchHealth}
                disabled={loadingHealth}
                className="p-1 rounded hover:bg-slate-900 text-slate-500 hover:text-white"
                title="Refresh Status"
              >
                <RefreshCw className={`w-3 h-3 ${loadingHealth ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] p-2 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div className="flex items-center gap-2 pr-2 min-w-0">
                  <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span className="font-bold text-slate-350 truncate">Metadata DB</span>
                </div>
                {renderStatusBadge(getServiceStatus('database'))}
              </div>

              <div className="flex items-center justify-between text-[11px] p-2 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div className="flex items-center gap-2 pr-2 min-w-0">
                  <HardDrive className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="font-bold text-slate-350 truncate">MinIO (Hot)</span>
                </div>
                {renderStatusBadge(getServiceStatus('minio'))}
              </div>

              <div className="flex items-center justify-between text-[11px] p-2 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div className="flex items-center gap-2 pr-2 min-w-0">
                  <HardDrive className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="font-bold text-slate-350 truncate">Seaweed (Warm)</span>
                </div>
                {renderStatusBadge(getServiceStatus('seaweedfs'))}
              </div>

              <div className="flex items-center justify-between text-[11px] p-2 bg-slate-950/40 border border-slate-900 rounded-xl">
                <div className="flex items-center gap-2 pr-2 min-w-0">
                  <HardDrive className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                  <span className="font-bold text-slate-350 truncate">Scality (Archive)</span>
                </div>
                {renderStatusBadge(getServiceStatus('scality'))}
              </div>
            </div>
          </div>

          {/* User Activity Log Feed Card (visible to standard users only as admin has it in tabs) */}
          {user?.role !== 'admin' && (
            <div className="bg-slate-900/40 border border-slate-900 rounded-3xl p-5 backdrop-blur-sm flex flex-col max-h-[300px] shadow-md">
              <div className="flex items-center justify-between border-b border-slate-850 pb-3 mb-3 shrink-0 select-none">
                <h3 className="font-outfit text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Server className="w-4 h-4 text-brand-400" /> Recent Actions
                </h3>
                <button
                  onClick={fetchActivities}
                  disabled={loadingActivities}
                  className="p-1 rounded hover:bg-slate-900 text-slate-500 hover:text-white"
                  title="Reload Logs"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingActivities ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-2 pr-0.5 scrollbar-thin">
                {loadingActivities ? (
                  <div className="text-center py-6 text-[10px] font-semibold text-slate-650">Loading feed...</div>
                ) : activities.length === 0 ? (
                  <div className="text-center py-6 text-[10px] font-semibold text-slate-600">No actions logged yet</div>
                ) : (
                  activities.map(log => (
                    <div key={log.id} className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-900 text-[10px] leading-relaxed">
                      <div className="flex items-center justify-between font-bold">
                        <span className="text-slate-200 capitalize">{log.action.replace('_', ' ')}</span>
                        <span className="text-slate-550 font-medium">
                          {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-slate-450 mt-1">{log.details}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* --- FLOATING WIDGETS & SYSTEM CONTEXTS --- */}

      {/* Absolute Positioning Right-click Context Menu */}
      {contextMenu.visible && (
        <div
          className="fixed bg-slate-900 border border-slate-850 rounded-2xl shadow-2xl py-1.5 z-50 w-44 animate-scaleIn select-none"
          style={{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => {
              setContextMenu({ ...contextMenu, visible: false })
              if (contextMenu.type === 'folder') {
                handleFolderClick(contextMenu.target)
              } else {
                setActiveDrawerFile(contextMenu.target)
              }
            }}
            className="w-full text-left px-4 py-2 text-xs text-slate-350 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
          >
            <FolderOpen className="w-3.5 h-3.5 text-brand-400" />
            <span>Open</span>
          </button>

          {contextMenu.type === 'file' && (
            <button
              onClick={() => {
                setContextMenu({ ...contextMenu, visible: false })
                handlePreviewFile(contextMenu.target)
              }}
              className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
            >
              <Eye className="w-3.5 h-3.5 text-sky-400" />
              <span>Preview</span>
            </button>
          )}

          {contextMenu.type === 'file' && (
            <button
              onClick={() => {
                setContextMenu({ ...contextMenu, visible: false })
                handleDownloadFile(contextMenu.target)
              }}
              className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span>Download</span>
            </button>
          )}

          <button
            onClick={() => {
              setContextMenu({ ...contextMenu, visible: false })
              setRenameTarget({
                type: contextMenu.type,
                id: contextMenu.target.id,
                name: contextMenu.target.name
              })
              setRenameName(contextMenu.target.name)
            }}
            className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
          >
            <Edit3 className="w-3.5 h-3.5 text-amber-400" />
            <span>Rename</span>
          </button>

          {contextMenu.type === 'file' && (
            <>
              <button
                onClick={() => {
                  setContextMenu({ ...contextMenu, visible: false })
                  navigator.clipboard.writeText(contextMenu.target.name)
                  addToast('Name copied to clipboard', 'info')
                }}
                className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
              >
                <Copy className="w-3.5 h-3.5 text-indigo-400" />
                <span>Copy Name</span>
              </button>

              <button
                onClick={() => {
                  setContextMenu({ ...contextMenu, visible: false })
                  setActiveDrawerFile(contextMenu.target)
                }}
                className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
              >
                <Info className="w-3.5 h-3.5 text-sky-400" />
                <span>Properties</span>
              </button>

              <button
                onClick={() => {
                  setContextMenu({ ...contextMenu, visible: false })
                  setActiveDrawerFile(contextMenu.target)
                }}
                className="w-full text-left px-4 py-2 text-xs text-slate-355 hover:text-white hover:bg-slate-850/40 flex items-center gap-2 transition-colors font-bold"
              >
                <Map className="w-3.5 h-3.5 text-purple-400" />
                <span>Storage Journey</span>
              </button>
            </>
          )}

          <div className="border-t border-slate-850 my-1"></div>

          <button
            onClick={() => {
              setContextMenu({ ...contextMenu, visible: false })
              if (contextMenu.type === 'folder') {
                handleDeleteFolder(contextMenu.target)
              } else {
                handleDeleteFile(contextMenu.target)
              }
            }}
            className="w-full text-left px-4 py-2 text-xs text-rose-450 hover:bg-rose-500/10 hover:text-rose-350 flex items-center gap-2 transition-colors font-bold"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Delete</span>
          </button>
        </div>
      )}

      {/* Slide-out File Details Drawer */}
      {activeDrawerFile && (
        <>
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-[2px] z-40 transition-all"
            onClick={() => setActiveDrawerFile(null)}
          ></div>

          <div className="fixed top-0 right-0 h-full w-96 bg-slate-900 border-l border-slate-850 shadow-2xl z-50 flex flex-col animate-slideInRight text-slate-200">
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-slate-850 bg-slate-950/40 shrink-0 select-none">
              <h3 className="font-outfit text-sm font-bold text-white flex items-center gap-2">
                <Info className="w-4.5 h-4.5 text-brand-400" />
                <span>File Details</span>
              </h3>
              <button
                onClick={() => setActiveDrawerFile(null)}
                className="p-1 hover:bg-slate-850 text-slate-450 hover:text-white rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Properties summary & Timeline list */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6 scrollbar-thin">
              <div className="flex flex-col items-center text-center p-4 bg-slate-950/20 border border-slate-850/50 rounded-2xl relative select-text">
                <div className="p-3 bg-slate-900 border border-slate-850 rounded-xl mb-3 shadow-inner">
                  {getFileIcon(activeDrawerFile)}
                </div>
                <h4 className="text-xs font-bold text-white max-w-xs truncate" title={activeDrawerFile.name}>
                  {activeDrawerFile.name}
                </h4>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider mt-1.5">
                  {activeDrawerFile.extension || 'file'}
                </span>
              </div>

              {/* Specs List */}
              <div className="space-y-3">
                <h5 className="text-[9px] font-bold text-slate-550 uppercase tracking-widest select-none">Properties</h5>
                <div className="space-y-2.5 divide-y divide-slate-850/40 text-xs">
                  <div className="flex items-center justify-between pt-2.5 first:pt-0">
                    <span className="text-slate-450">File Name</span>
                    <span className="font-bold text-slate-300 truncate max-w-[180px]" title={activeDrawerFile.name}>{activeDrawerFile.name}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2.5">
                    <span className="text-slate-450">File Size</span>
                    <span className="font-bold text-slate-300">{formatBytes(activeDrawerFile.size)}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2.5">
                    <span className="text-slate-450">Upload Date</span>
                    <span className="font-bold text-slate-300">
                      {new Date(activeDrawerFile.upload_date).toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2.5">
                    <span className="text-slate-450">Current Storage</span>
                    <span className="font-bold text-slate-300 uppercase">
                      {activeDrawerFile.current_backend || 'MinIO'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2.5">
                    <span className="text-slate-450">Storage Tier</span>
                    <span className="font-bold">
                      {activeDrawerFile.current_tier === 'hot' ? <span className="text-amber-400">🔥 Hot Tier</span> :
                       activeDrawerFile.current_tier === 'warm' ? <span className="text-cyan-400">🌤 Warm Tier</span> :
                       <span className="text-purple-400">❄ Archive Tier</span>}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2.5">
                    <span className="text-slate-450">Checksum (SHA256)</span>
                    <span className="font-mono text-[9px] text-brand-400 max-w-[150px] truncate" title={activeDrawerFile.checksum}>
                      {activeDrawerFile.checksum || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Journey Timeline */}
              <div className="space-y-4 pt-3">
                <h5 className="text-[9px] font-bold text-slate-550 uppercase tracking-widest flex items-center gap-1.5 select-none">
                  <Map className="w-3.5 h-3.5 text-brand-400" /> Storage Journey
                </h5>
                <StorageTimeline file={activeDrawerFile} />
              </div>
            </div>

            {/* Quick Actions Footer */}
            <div className="p-4 bg-slate-950/80 border-t border-slate-850 shrink-0 grid grid-cols-3 gap-2 shrink-0 select-none">
              <button
                onClick={() => handleDownloadFile(activeDrawerFile)}
                className="flex flex-col items-center justify-center gap-1 p-2 text-[10px] font-bold rounded-xl bg-slate-900 border border-slate-800 text-emerald-400 hover:bg-slate-850 hover:text-emerald-300 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download</span>
              </button>
              <button
                onClick={() => handlePreviewFile(activeDrawerFile)}
                className="flex flex-col items-center justify-center gap-1 p-2 text-[10px] font-bold rounded-xl bg-slate-900 border border-slate-800 text-sky-400 hover:bg-slate-850 hover:text-sky-300 transition-colors"
              >
                <Eye className="w-4 h-4" />
                <span>Preview</span>
              </button>
              <button
                onClick={() => {
                  const file = activeDrawerFile
                  handleDeleteFile(file)
                }}
                className="flex flex-col items-center justify-center gap-1 p-2 text-[10px] font-bold rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-455 hover:bg-rose-500/20 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Floating Upload Queue list */}
      {uploadQueue.length > 0 && (
        <div className={`fixed bottom-6 right-6 w-80 bg-slate-900 border border-slate-850 rounded-2xl shadow-2xl z-40 transition-all duration-300 overflow-hidden flex flex-col ${
          minimizeUploadQueue ? 'h-12' : 'max-h-72'
        }`}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-900 shrink-0 select-none">
            <h4 className="text-xs font-bold text-slate-200 flex items-center gap-2">
              {uploadQueue.some(u => u.status === 'uploading') ? (
                <Loader className="w-3.5 h-3.5 text-brand-400 animate-spin" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              )}
              <span>Uploads ({uploadQueue.filter(u => u.status === 'uploading').length} active)</span>
            </h4>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setMinimizeUploadQueue(!minimizeUploadQueue)}
                className="p-1 text-slate-450 hover:text-white rounded hover:bg-slate-900 transition-colors"
              >
                {minimizeUploadQueue ? <ChevronDown className="w-4 h-4" /> : <ChevronDown className="w-4 h-4 rotate-180" />}
              </button>
              <button
                onClick={() => setUploadQueue([])}
                className="p-1 text-slate-450 hover:text-rose-400 rounded hover:bg-slate-900 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Items list */}
          {!minimizeUploadQueue && (
            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 divide-y divide-slate-850/40 scrollbar-thin">
              {uploadQueue.map(item => (
                <div key={item.id} className="pt-2.5 first:pt-0 text-[11px]">
                  <div className="flex items-center justify-between font-bold text-slate-200">
                    <span className="truncate max-w-[180px]">{item.name}</span>
                    <span className="text-[10px] font-mono text-slate-500 shrink-0">
                      {item.status === 'uploading' ? `${item.progress}%` : item.status}
                    </span>
                  </div>
                  
                  {item.status === 'uploading' && (
                    <>
                      <div className="w-full bg-slate-950 rounded-full h-1 mt-2 overflow-hidden border border-slate-900">
                        <div className="bg-brand-500 h-full transition-all duration-300" style={{ width: `${item.progress}%` }}></div>
                      </div>
                      <div className="flex items-center justify-between text-[9px] text-slate-550 mt-1.5 font-bold uppercase tracking-wider">
                        <span>{item.speed}</span>
                        <span>{item.remainingTime}</span>
                        <button
                          onClick={() => item.cancelTokenSource?.cancel()}
                          className="text-rose-455 hover:text-rose-400 font-bold hover:underline"
                        >
                          Cancel
                        </button>
                      </div>
                    </>
                  )}

                  {item.status === 'completed' && (
                    <p className="text-[9px] text-emerald-450 flex items-center gap-1 mt-1.5 font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Upload Complete
                    </p>
                  )}

                  {item.status === 'cancelled' && (
                    <p className="text-[9px] text-slate-500 flex items-center gap-1 mt-1.5 font-bold">
                      <XCircle className="w-3.5 h-3.5" /> Cancelled
                    </p>
                  )}

                  {item.status === 'failed' && (
                    <p className="text-[9px] text-rose-455 flex items-center gap-1 mt-1.5 font-bold">
                      <AlertCircle className="w-3.5 h-3.5" /> Failed
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Floating stackable custom toast stack */}
      {toasts.length > 0 && (
        <div className="fixed bottom-6 left-6 z-50 flex flex-col gap-2 pointer-events-none select-none max-w-sm">
          {toasts.map(t => (
            <div
              key={t.id}
              className={`p-3.5 rounded-xl border shadow-xl text-xs font-bold flex items-center gap-2.5 animate-toastSlideIn pointer-events-auto ${
                t.type === 'error' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
                t.type === 'info' ? 'bg-slate-900 border-slate-800 text-sky-400' :
                'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              }`}
            >
              {t.type === 'error' ? <AlertCircle className="w-4 h-4 shrink-0" /> :
               t.type === 'info' ? <Info className="w-4 h-4 shrink-0" /> :
               <CheckCircle2 className="w-4 h-4 shrink-0" />}
              <span>{t.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Inline File Preview Modal Dialog */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-sm animate-fadeIn select-none">
          <div className="w-full max-w-4xl bg-slate-900 border border-slate-850 rounded-3xl p-5 shadow-2xl relative flex flex-col h-[80vh]">
            <button
              onClick={handleClosePreview}
              className="absolute top-4 right-4 p-1 bg-slate-950 border border-slate-850 hover:bg-slate-800 text-slate-450 hover:text-white rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-outfit text-sm font-bold text-white mb-4 truncate pr-12 flex items-center gap-2">
              <Eye className="w-4.5 h-4.5 text-sky-400" />
              <span>Preview: {previewFile.name}</span>
            </h3>
            
            <div className="flex-1 min-h-0 bg-slate-950 rounded-2xl border border-slate-850/60 overflow-hidden flex items-center justify-center relative p-2 select-text">
              {previewLoading ? (
                <div className="flex flex-col items-center gap-2 text-slate-500">
                  <Loader className="w-8 h-8 animate-spin text-brand-400" />
                  <span className="text-xs">Loading preview...</span>
                </div>
              ) : previewContent ? (
                <pre className="w-full h-full p-4 font-mono text-xs text-slate-350 overflow-auto whitespace-pre-wrap select-text selection:bg-brand-500/30">
                  {previewContent}
                </pre>
              ) : previewUrl && ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(previewFile.extension?.toLowerCase()) ? (
                <img src={previewUrl} alt={previewFile.name} className="max-w-full max-h-full object-contain rounded-lg" />
              ) : previewUrl && previewFile.extension?.toLowerCase() === 'pdf' ? (
                <iframe src={previewUrl} className="w-full h-full border-0 rounded-lg" title={previewFile.name} />
              ) : (
                <div className="text-center p-6 text-slate-500 flex flex-col items-center gap-3">
                  <AlertCircle className="w-10 h-10 text-slate-450" />
                  <p className="text-xs font-semibold">No visual preview available for this file type.</p>
                  <button
                    onClick={() => handleDownloadFile(previewFile)}
                    className="px-4 py-2 text-xs font-bold rounded-xl bg-brand-655 hover:bg-brand-600 text-white flex items-center gap-2 shadow-md"
                  >
                    <Download className="w-4 h-4" /> Download File
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hidden File/Folder Inputs for Uploads */}
      <input
        id="file-upload-input"
        type="file"
        onChange={handleFileUpload}
        className="hidden"
      />
      <input
        id="folder-upload-input"
        type="file"
        webkitdirectory="true"
        directory="true"
        multiple
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* --- MODALS SECTION --- */}

      {/* Folder Creation Modal */}
      {showFolderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-850 rounded-3xl p-6 shadow-2xl relative">
            <button 
              onClick={() => setShowFolderModal(false)}
              className="absolute top-4 right-4 text-slate-450 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-outfit text-base font-bold text-white mb-4">Create Folder</h3>
            <form onSubmit={handleCreateFolder} className="space-y-4">
              <input
                type="text"
                required
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Folder name"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-850 rounded-xl text-slate-200 placeholder-slate-650 text-xs focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-brand-655 hover:bg-brand-600 text-white text-xs font-bold transition-all shadow-md shadow-brand-655/15"
              >
                Create
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {renameTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-850 rounded-3xl p-6 shadow-2xl relative">
            <button 
              onClick={() => setRenameTarget(null)}
              className="absolute top-4 right-4 text-slate-450 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="font-outfit text-base font-bold text-white mb-4">
              Rename {renameTarget.type === 'folder' ? 'Folder' : 'File'}
            </h3>
            <form onSubmit={handleRenameSubmit} className="space-y-4">
              <input
                type="text"
                required
                value={renameName}
                onChange={(e) => setRenameName(e.target.value)}
                placeholder="New name"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-850 rounded-xl text-slate-200 placeholder-slate-655 text-xs focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-brand-655 hover:bg-brand-600 text-white text-xs font-bold transition-all shadow-md"
              >
                Rename
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 bg-slate-950 z-10 relative">
        <div className="max-w-7xl mx-auto px-4 text-center text-[10px] text-slate-650 uppercase tracking-widest font-bold">
          CloudVault &copy; {new Date().getFullYear()} &bull; Major Project Console UI.
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          } />
          <Route path="/register" element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
