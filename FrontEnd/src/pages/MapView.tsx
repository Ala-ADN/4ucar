import { useState } from "react";
import { 
  ComposableMap, 
  Geographies, 
  Geography, 
  Marker, 
  ZoomableGroup 
} from "react-simple-maps";
import { motion, AnimatePresence } from "motion/react";
import { MapPin, X, GraduationCap, Users, TrendingUp, FlaskConical, AlertCircle } from "lucide-react";
import { Institution } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { cn } from "@/src/lib/utils";
import { Badge } from "@/src/components/ui/StatusDot";
import { Link } from "react-router-dom";

// Tunisia GeoJSON URL (simplified version)
const geoUrl = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/pays/tunisie/tunisie.json";

export function MapView() {
  const institutions = institutionsData as Institution[];
  const [selectedInst, setSelectedInst] = useState<Institution | null>(null);
  const [position, setPosition] = useState({ coordinates: [9.5375, 33.8869], zoom: 3 });

  function handleZoomIn() {
    if (position.zoom >= 8) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom * 1.5 }));
  }

  function handleZoomOut() {
    if (position.zoom <= 1) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom / 1.5 }));
  }

  function handleReset() {
    setPosition({ coordinates: [9.5375, 33.8869], zoom: 3 });
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return '#22C55E';
      case 'warning': return '#EAB308';
      case 'critical': return '#EF4444';
      default: return '#3B82F6';
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] w-full bg-surface rounded-2xl shadow-card overflow-hidden relative flex flex-col">
      <div className="absolute top-6 left-6 z-10">
        <h2 className="text-xl font-bold text-text-primary">Carte de surveillance UCAR</h2>
        <p className="text-sm text-text-muted">Explorez l'état du réseau en temps réel à travers la Tunisie</p>
      </div>

      <div className="flex-1 map-bg relative">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 3000,
            center: [9.5375, 34.5]
          }}
          className="w-full h-full outline-none"
        >
          <ZoomableGroup
            zoom={position.zoom}
            center={position.coordinates as [number, number]}
            onMoveEnd={(pos) => setPosition(pos)}
          >
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill="#EFF6FF"
                    stroke="#BFDBFE"
                    strokeWidth={0.5}
                    style={{
                      default: { outline: "none" },
                      hover: { fill: "#DBEAFE", outline: "none" },
                      pressed: { outline: "none" },
                    }}
                  />
                ))
              }
            </Geographies>

            {institutions.map((inst, index) => (
              <Marker key={inst.code} coordinates={inst.coords}>
                {/* Pulse ring for warning/critical */}
                {(inst.global_health === 'critical' || inst.global_health === 'warning') && (
                  <motion.circle
                    r={12 / (position.zoom * 0.5)}
                    fill={getStatusColor(inst.global_health)}
                    opacity={0.3}
                    animate={{ scale: [1, 1.8, 1], opacity: [0.3, 0, 0.3] }}
                    transition={{ duration: 2.5, repeat: Infinity, delay: index * 0.2 }}
                  />
                )}
                
                <motion.circle
                  r={6 / (position.zoom * 0.5)}
                  fill={getStatusColor(inst.global_health)}
                  stroke="white"
                  strokeWidth={2 / (position.zoom * 0.5)}
                  whileHover={{ scale: 1.5 }}
                  cursor="pointer"
                  onClick={() => setSelectedInst(inst)}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.5 + index * 0.05 }}
                />

                {position.zoom > 4 && (
                  <text
                    y={-10 / (position.zoom * 0.5)}
                    textAnchor="middle"
                    className="select-none pointer-events-none fill-text-secondary font-bold"
                    style={{ fontSize: 8 / (position.zoom * 0.5) }}
                  >
                    {inst.code}
                  </text>
                )}
              </Marker>
            ))}
          </ZoomableGroup>
        </ComposableMap>

        {/* Map Controls */}
        <div className="absolute bottom-6 left-6 flex flex-col gap-2 bg-surface p-1 rounded-lg shadow-md border border-border">
          <button onClick={handleZoomIn} className="p-2 hover:bg-surface-hover rounded-md text-text-secondary transition-colors" title="Zoom avant">+</button>
          <div className="h-[1px] bg-border mx-2" />
          <button onClick={handleZoomOut} className="p-2 hover:bg-surface-hover rounded-md text-text-secondary transition-colors" title="Zoom arrière">−</button>
          <div className="h-[1px] bg-border mx-2" />
          <button onClick={handleReset} className="p-2 hover:bg-surface-hover rounded-md text-text-secondary transition-colors" title="Réinitialiser">⌂</button>
        </div>

        {/* Legend */}
        <div className="absolute bottom-6 right-6 bg-surface/80 backdrop-blur-sm p-3 rounded-xl border border-border shadow-md">
          <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">Légende</h3>
          <div className="flex flex-col gap-2">
            <LegendItem color="#22C55E" label="Sain" />
            <LegendItem color="#EAB308" label="Attention" />
            <LegendItem color="#EF4444" label="Critique" />
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <AnimatePresence>
        {selectedInst && (
          <motion.div
            initial={{ x: 340, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 340, opacity: 0 }}
            transition={{ type: "spring", damping: 20, stiffness: 100 }}
            className="absolute top-6 right-6 bottom-6 w-80 bg-surface shadow-lg rounded-2xl border border-border p-6 flex flex-col gap-6 z-20"
          >
            <div className="flex justify-between items-start">
              <div>
                <Badge variant={selectedInst.type === 'grande_ecole' ? 'info' : (selectedInst.type === 'faculte' ? 'purple' : 'amber')}>
                  {selectedInst.type.replace('_', ' ')}
                </Badge>
                <h3 className="text-xl font-bold text-text-primary mt-2">{selectedInst.code}</h3>
                <p className="text-xs text-text-muted mt-1 leading-relaxed">{selectedInst.name}</p>
              </div>
              <button 
                onClick={() => setSelectedInst(null)}
                className="p-1 hover:bg-surface-hover rounded-full text-text-muted"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex items-center gap-3 text-xs text-text-secondary">
              <span className="flex items-center gap-1.5"><MapPin size={14} className="text-blue-500" /> {selectedInst.city}</span>
              <span className="text-border-strong">|</span>
              <span className="flex items-center gap-1.5"><Users size={14} className="text-blue-500" /> {selectedInst.students.toLocaleString()}</span>
            </div>

            <div className="space-y-4">
              <h4 className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Aperçu KPI</h4>
              <div className="space-y-3">
                <MiniKPIRow icon={TrendingUp} label="Réussite" value={selectedInst.kpi_snapshot?.taux_reussite ?? 0} suffix="%" />
                <MiniKPIRow icon={GraduationCap} label="Budget exec." value={selectedInst.kpi_snapshot?.budget_execution ?? 0} suffix="%" />
                <MiniKPIRow icon={Users} label="Encadrement" value={`1 / ${selectedInst.kpi_snapshot?.taux_encadrement ?? 0}`} />
                <MiniKPIRow icon={FlaskConical} label="Recherche" value={selectedInst.kpi_snapshot?.publications_indexees ?? 0} suffix=" / an" />
              </div>
            </div>

            {selectedInst.alerts_active && selectedInst.alerts_active > 0 && (
              <div className="bg-status-critical-bg p-3 rounded-lg border border-status-critical/10 flex items-center gap-3">
                <AlertCircle size={18} className="text-status-critical" />
                <span className="text-xs font-bold text-status-critical">{selectedInst.alerts_active} alertes actives</span>
              </div>
            )}

            <Link 
              to={`/institutions/${selectedInst.code}`}
              className="mt-auto w-full bg-blue-500 text-white py-3 rounded-xl font-bold text-sm text-center hover:bg-blue-600 transition-colors shadow-md shadow-blue-500/20"
            >
              Voir le tableau de bord →
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[11px] font-medium text-text-secondary">{label}</span>
    </div>
  );
}

function MiniKPIRow({ icon: Icon, label, value, suffix = "" }: { icon: any; label: string; value: string | number; suffix?: string }) {
  const numericValue = typeof value === 'number' ? value : 0;
  
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center text-[11px]">
        <span className="flex items-center gap-1.5 text-text-secondary font-medium"><Icon size={12} className="text-text-muted" /> {label}</span>
        <span className="font-bold text-text-primary">{value}{suffix}</span>
      </div>
      {typeof value === 'number' && (
        <div className="h-1.5 bg-off-white rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${numericValue}%` }}
            transition={{ duration: 1, delay: 0.2 }}
            className={cn(
              "h-full rounded-full",
              numericValue > 75 ? "bg-status-good" : (numericValue > 50 ? "bg-status-medium" : "bg-status-critical")
            )}
          />
        </div>
      )}
    </div>
  );
}
