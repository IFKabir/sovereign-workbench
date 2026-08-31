'use client';

import { motion } from 'framer-motion';
import { Activity, Database, Server, Clock, CheckCircle } from 'lucide-react';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export default function DashboardPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto min-h-full">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent-cyan to-accent-emerald">
          Sovereign AI Workbench
        </h1>
        <p className="text-accent-amber mt-2 font-mono text-sm tracking-wider uppercase">
          MRPL · SIH26117 · Air-Gapped Industrial AI
        </p>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10"
      >
        {[
          { label: 'Total Queries', value: '14,203', icon: Activity, color: 'text-accent-cyan' },
          { label: 'Active Models', value: 'vLLM / YOLO', icon: Server, color: 'text-accent-emerald' },
          { label: 'Avg Chain Length', value: '4.2 Nodes', icon: Database, color: 'text-accent-amber' },
          { label: 'Uptime (Air-Gapped)', value: '99.99%', icon: Clock, color: 'text-gray-300' },
        ].map((stat, i) => (
          <motion.div key={i} variants={item} className="glass-panel p-6 rounded-xl border border-sovereign-border hover:bg-sovereign-surface/80 transition-colors border-t-2 border-t-sovereign-border hover:border-t-accent-cyan">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
                <h3 className="text-2xl font-bold text-gray-100">{stat.value}</h3>
              </div>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
          </motion.div>
        ))}
      </motion.div>

      <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={item} className="lg:col-span-2 glass-panel border border-sovereign-border rounded-xl p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center text-gray-200"><Server className="mr-3 w-5 h-5 text-accent-cyan"/> System Status</h2>
          <div className="space-y-4">
            {[
              { name: 'vLLM Service (Llama-3-70B)', status: 'Healthy', load: '45%' },
              { name: 'YOLOv10 P&ID Detector', status: 'Healthy', load: '12%' },
              { name: 'Qdrant Vector DB', status: 'Healthy', load: '8%' },
              { name: 'BGE-M3 Embeddings', status: 'Healthy', load: '22%' },
            ].map((service, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-sovereign-surface/50 rounded-lg border border-sovereign-border">
                <span className="font-mono text-sm text-gray-300">{service.name}</span>
                <div className="flex items-center space-x-6">
                  <span className="text-xs text-gray-400">Load: <span className="text-gray-200">{service.load}</span></span>
                  <span className="flex items-center text-xs font-medium text-accent-emerald bg-accent-emerald/10 px-2 py-1 rounded border border-accent-emerald/20">
                    <CheckCircle className="w-3 h-3 mr-1.5" /> {service.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div variants={item} className="glass-panel border border-sovereign-border rounded-xl p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center text-gray-200"><Activity className="mr-3 w-5 h-5 text-accent-amber"/> Recent Activity</h2>
          <div className="space-y-4">
            {[
              { user: 'Operator A', action: 'Compliance Check', time: '2m ago' },
              { user: 'Engineer B', action: 'P&ID Extraction', time: '15m ago' },
              { user: 'System', action: 'Model Weight Sync', time: '1h ago' },
              { user: 'Auditor C', action: 'Trace Verification', time: '2h ago' },
            ].map((act, i) => (
              <div key={i} className="border-l-2 border-accent-cyan pl-4 py-1">
                <p className="text-sm font-medium text-gray-200">{act.action}</p>
                <p className="text-xs text-gray-400 mt-1">{act.user} · {act.time}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
