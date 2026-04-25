import { useState } from 'react';
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from 'react-simple-maps';
import { MapPin, X, GraduationCap, Users, TrendingUp, FlaskConical, AlertCircle } from 'lucide-react';
import { Institution } from '@/src/types';
import institutionsData from '@/src/data/institutions.json';
import { cn } from '@/src/lib/utils';
import { Badge } from '@/src/components/ui/StatusDot';
import { Link } from 'react-router-dom';

const geoUrl = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/pays/tunisie/tunisie.json';

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
      case 'good':
        return '#16A34A';
      case 'warning':
        return '#D97706';
      case 'critical':
        return '#DC2626';
      default:
        return '#1D4ED8';
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] w-full bg-white rounded-md border border-slate-200 overflow-hidden relative flex flex-col">
      <div className="absolute top-4 left-4 z-10 bg-white/95 border border-slate-200 rounded-md p-3">
        <h2 className="text-lg font-semibold text-slate-900">Carte de surveillance UCAR</h2>
        <p className="text-sm text-slate-600">Etat du reseau universitaire en Tunisie</p>
      </div>

      <div className="flex-1 map-bg relative">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 3000,
            center: [9.5375, 34.5],
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
                    fill="#F8FAFC"
                    stroke="#CBD5E1"
                    strokeWidth={0.6}
                    style={{
                      default: { outline: 'none' },
                      hover: { fill: '#E2E8F0', outline: 'none' },
                      pressed: { outline: 'none' },
                    }}
                  />
                ))
              }
            </Geographies>

            {institutions.map((inst) => (
              <Marker key={inst.code} coordinates={inst.coords}>
                <circle
                  r={6 / (position.zoom * 0.5)}
                  fill={getStatusColor(inst.global_health)}
                  stroke="white"
                  strokeWidth={2 / (position.zoom * 0.5)}
                  cursor="pointer"
                  onClick={() => setSelectedInst(inst)}
                />

                {position.zoom > 4 && (
                  <text
                    y={-10 / (position.zoom * 0.5)}
                    textAnchor="middle"
                    className="select-none pointer-events-none"
                    style={{ fontSize: 8 / (position.zoom * 0.5), fill: '#334155', fontWeight: 500 }}
                  >
                    {inst.code}
                  </text>
                )}
              </Marker>
            ))}
          </ZoomableGroup>
        </ComposableMap>

        <div className="absolute bottom-4 left-4 flex flex-col gap-1 bg-white p-1 rounded-md border border-slate-300">
          <button onClick={handleZoomIn} className="p-2 hover:bg-slate-100 rounded text-slate-700 transition-colors duration-150" title="Zoom avant">+</button>
          <div className="h-px bg-slate-200 mx-1" />
          <button onClick={handleZoomOut} className="p-2 hover:bg-slate-100 rounded text-slate-700 transition-colors duration-150" title="Zoom arriere">-</button>
          <div className="h-px bg-slate-200 mx-1" />
          <button onClick={handleReset} className="p-2 hover:bg-slate-100 rounded text-slate-700 transition-colors duration-150" title="Reinitialiser">R</button>
        </div>

        <div className="absolute bottom-4 right-4 bg-white p-3 rounded-md border border-slate-200">
          <h3 className="text-xs font-medium text-slate-700 mb-2">Legende</h3>
          <div className="flex flex-col gap-1.5">
            <LegendItem color="#16A34A" label="Sain" />
            <LegendItem color="#D97706" label="Attention" />
            <LegendItem color="#DC2626" label="Critique" />
          </div>
        </div>
      </div>

      {selectedInst && (
        <div className="absolute top-4 right-4 bottom-4 w-80 bg-white rounded-md border border-slate-200 p-5 flex flex-col gap-5 z-20">
          <div className="flex justify-between items-start">
            <div>
              <Badge variant={selectedInst.type === 'grande_ecole' ? 'info' : selectedInst.type === 'faculte' ? 'purple' : 'amber'}>
                {selectedInst.type.replace('_', ' ')}
              </Badge>
              <h3 className="text-xl font-semibold text-slate-900 mt-2">{selectedInst.code}</h3>
              <p className="text-sm text-slate-600 mt-1 leading-relaxed">{selectedInst.name}</p>
            </div>
            <button
              onClick={() => setSelectedInst(null)}
              className="p-1 hover:bg-slate-100 rounded text-slate-500"
              aria-label="Fermer le panneau"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex items-center gap-3 text-sm text-slate-700">
            <span className="flex items-center gap-1.5"><MapPin size={14} /> {selectedInst.city}</span>
            <span className="text-slate-400">|</span>
            <span className="flex items-center gap-1.5"><Users size={14} /> {selectedInst.students.toLocaleString()}</span>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-800">Apercu KPI</h4>
            <div className="space-y-2">
              <MiniKPIRow icon={TrendingUp} label="Reussite" value={selectedInst.kpi_snapshot?.taux_reussite ?? 0} suffix="%" />
              <MiniKPIRow icon={GraduationCap} label="Budget exec." value={selectedInst.kpi_snapshot?.budget_execution ?? 0} suffix="%" />
              <MiniKPIRow icon={Users} label="Encadrement" value={`1 / ${selectedInst.kpi_snapshot?.taux_encadrement ?? 0}`} />
              <MiniKPIRow icon={FlaskConical} label="Recherche" value={selectedInst.kpi_snapshot?.publications_indexees ?? 0} suffix=" / an" />
            </div>
          </div>

          {selectedInst.alerts_active && selectedInst.alerts_active > 0 && (
            <div className="bg-red-50 p-3 rounded-md border border-red-200 flex items-center gap-2">
              <AlertCircle size={16} className="text-red-700" />
              <span className="text-sm font-medium text-red-700">{selectedInst.alerts_active} alertes actives</span>
            </div>
          )}

          <Link
            to={`/institutions/${selectedInst.code}`}
            className="mt-auto w-full bg-blue-800 text-white py-2 rounded-md font-medium text-sm text-center hover:bg-blue-900 transition-colors duration-150"
          >
            Voir le tableau de bord
          </Link>
        </div>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-xs text-slate-700">{label}</span>
    </div>
  );
}

function MiniKPIRow({
  icon: Icon,
  label,
  value,
  suffix = '',
}: {
  icon: any;
  label: string;
  value: string | number;
  suffix?: string;
}) {
  const numericValue = typeof value === 'number' ? value : 0;

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-sm">
        <span className="flex items-center gap-1.5 text-slate-700"><Icon size={12} className="text-slate-500" /> {label}</span>
        <span className="font-medium text-slate-900">{value}{suffix}</span>
      </div>
      {typeof value === 'number' && (
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            style={{ width: `${numericValue}%` }}
            className={cn(
              'h-full rounded-full',
              numericValue > 75 ? 'bg-green-700' : numericValue > 50 ? 'bg-amber-500' : 'bg-red-600'
            )}
          />
        </div>
      )}
    </div>
  );
}
