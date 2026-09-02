'use client';

import { motion } from 'framer-motion';
import { Shield, BookOpen, Search, Lock, ArrowRight, Eye, Calculator, FileText } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getSession, getApiHeaders, type MRPLSession, getPlantUnitLabel } from '@/lib/session';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

const quickLaunchers = [
  {
    title: 'P&ID Safety & Isolation Check',
    description: 'Inspect control valve bypass arrangements for DBB compliance, identify unmonitored loops.',
    icon: Eye,
    color: 'text-accent-amber',
    bg: 'bg-accent-amber/5',
    border: 'border-accent-amber/20 hover:border-accent-amber/50',
    href: '/chat?q=Inspect+the+CDU+bypass+line+schematic.+Does+Valve+CV-101+follow+a+compliant+Double+Block+and+Bleed+arrangement%3F',
  },
  {
    title: 'OISD Separation Distance Lookup',
    description: 'Query minimum safe distances between process units, tanks, and buildings per OISD-118.',
    icon: BookOpen,
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/5',
    border: 'border-accent-cyan/20 hover:border-accent-cyan/50',
    href: '/chat?q=What+is+the+minimum+safe+separation+distance+between+a+furnace+and+a+storage+tank+under+OISD-118%3F',
  },
  {
    title: 'Calculate Pressure Drop / Orifice Sizing',
    description: 'Run verified engineering calculations in an isolated sandbox with Darcy-Weisbach, API-520 formulas.',
    icon: Calculator,
    color: 'text-accent-emerald',
    bg: 'bg-accent-emerald/5',
    border: 'border-accent-emerald/20 hover:border-accent-emerald/50',
    href: '/chat?q=Calculate+the+pressure+drop+across+a+100m+crude+oil+pipeline+using+Darcy-Weisbach+equation',
  },
  {
    title: 'Shift Handover Digest',
    description: 'Extract and summarize equipment status, near-misses, and outstanding work orders from handover reports.',
    icon: FileText,
    color: 'text-purple-400',
    bg: 'bg-purple-400/5',
    border: 'border-purple-400/20 hover:border-purple-400/50',
    href: '/chat?q=Summarize+the+equipment+issues+and+near-miss+events+from+the+shift+handover+report',
  },
];

export default function DashboardPage() {
  const [session, setSession] = useState<MRPLSession | null>(null);
  const [engineHealth, setEngineHealth] = useState<string>('Operational');
  const [auditBlockCount, setAuditBlockCount] = useState<number>(0);

  useEffect(() => {
    setSession(getSession());

    // Fetch dynamic telemetry
    const fetchTelemetry = async () => {
      try {
        const healthRes = await fetch('/health/ready');
        if (healthRes.ok) {
          const hData = await healthRes.json();
          if (hData.status === 'ready') setEngineHealth('Operational');
        }

        const auditRes = await fetch('/api/v1/audit/stats', { headers: getApiHeaders() });
        if (auditRes.ok) {
          const aData = await auditRes.json();
          setAuditBlockCount(aData.total_blocks || 0);
        }
      } catch (err) {
        console.error('Failed to fetch dashboard telemetry:', err);
      }
    };

    fetchTelemetry();
  }, []);

  const statusCards = [
    {
      label: 'Sovereign Engine Status',
      value: engineHealth,
      detail: '100% On-Premise (Zero Network Egress)',
      icon: Shield,
      color: 'text-accent-emerald',
      borderColor: 'border-t-accent-emerald',
      pulseColor: 'bg-accent-emerald',
    },
    {
      label: 'Plant Standards Knowledge Base',
      value: 'Active',
      detail: 'OISD-118, OISD-105, API-520 — 107 Verified Clauses',
      icon: BookOpen,
      color: 'text-accent-cyan',
      borderColor: 'border-t-accent-cyan',
      pulseColor: 'bg-accent-cyan',
    },
    {
      label: 'Schematic Inspection Engine',
      value: 'Active',
      detail: 'ISA-5.1 P&ID Symbol Recognition (YOLOv11s)',
      icon: Search,
      color: 'text-accent-amber',
      borderColor: 'border-t-accent-amber',
      pulseColor: 'bg-accent-amber',
    },
    {
      label: 'Audit Ledger Height',
      value: `${auditBlockCount} Block${auditBlockCount === 1 ? '' : 's'}`,
      detail: 'SHA-256 Hash-Chained SQLite Ledger',
      icon: Lock,
      color: 'text-purple-400',
      borderColor: 'border-t-purple-400',
      pulseColor: 'bg-purple-400',
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-full">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
        <h1 className="text-3xl font-bold text-gray-100">
          Operations Dashboard
        </h1>
        <p className="text-gray-400 mt-1.5 text-sm">
          {session ? `${getPlantUnitLabel(session.plantUnit)} — ` : ''}Mangalore Refinery and Petrochemicals Limited
        </p>
      </motion.div>

      {/* Dynamic Status Cards */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10"
      >
        {statusCards.map((card, i) => (
          <motion.div
            key={i}
            variants={item}
            className={`glass-panel p-5 rounded-xl border border-sovereign-border hover:bg-sovereign-surface/80 transition-colors border-t-2 ${card.borderColor}`}
          >
            <div className="flex justify-between items-start mb-3">
              <card.icon className={`w-5 h-5 ${card.color}`} />
              <span className="flex items-center space-x-1.5">
                <span className={`w-2 h-2 rounded-full ${card.pulseColor} animate-pulse`} />
                <span className={`text-xs font-semibold ${card.color}`}>{card.value}</span>
              </span>
            </div>
            <h3 className="text-sm font-semibold text-gray-200 mb-1">{card.label}</h3>
            <p className="text-xs text-gray-400 leading-relaxed">{card.detail}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Operational Launchers */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
      >
        <h2 className="text-lg font-semibold text-gray-200 mb-4">Quick Operations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {quickLaunchers.map((launcher, i) => (
            <motion.div key={i} variants={item}>
              <Link
                href={launcher.href}
                className={`group block p-5 rounded-xl border ${launcher.border} ${launcher.bg} transition-all hover:shadow-lg`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg ${launcher.bg} border ${launcher.border}`}>
                      <launcher.icon className={`w-5 h-5 ${launcher.color}`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-200 group-hover:text-white transition-colors">
                        {launcher.title}
                      </h3>
                      <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                        {launcher.description}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className={`w-4 h-4 ${launcher.color} opacity-0 group-hover:opacity-100 transition-opacity mt-1`} />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

