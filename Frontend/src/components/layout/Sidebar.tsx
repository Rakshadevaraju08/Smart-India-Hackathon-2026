import { Home, BarChart2, Map, Bell, FileText, Settings, Activity } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="w-64 flex flex-col bg-slate-900/50 backdrop-blur-md border-r border-slate-700/50 h-screen text-slate-300">
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
        <Activity className="w-8 h-8 text-cyan-400" />
        <h1 className="text-xl font-bold text-white tracking-tight leading-tight">
          URBAN FLOOD <br/><span className="text-cyan-400 font-medium">NOWCASTING</span>
        </h1>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-2">
        <a href="#" className="flex items-center gap-3 px-4 py-3 bg-cyan-500/10 text-cyan-400 rounded-lg border border-cyan-500/20">
          <Home className="w-5 h-5" />
          <span className="font-medium">Dashboard</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <BarChart2 className="w-5 h-5" />
          <span>Analytics</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <Map className="w-5 h-5" />
          <span>Mapping</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
          <span>Alerts</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <FileText className="w-5 h-5" />
          <span>Reports</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 rounded-lg transition-colors">
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </a>
      </nav>

      <div className="p-6 border-t border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-700 overflow-hidden">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" alt="Admin User" />
          </div>
          <div>
            <div className="text-sm font-medium text-white">System Admin</div>
            <div className="text-xs text-slate-400">MoES / NCMRWF</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
