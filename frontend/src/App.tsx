import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { Monitoring } from './pages/Monitoring';
import { AIDiagnostics } from './pages/AIDiagnostics';
import { AlertsPage } from './pages/AlertsPage';
import { BackdoorModal } from './components/BackdoorModal';
import { apiService } from './services/api';
import { PlantSummary, TelemetryPoint, SystemAlert } from './types/solar';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [isBackdoorOpen, setIsBackdoorOpen] = useState<boolean>(false);

  // Estado limpio por defecto en CERO
  const [summary, setSummary] = useState<PlantSummary>({
    plant_id: 'plant-01',
    name: 'Planta Solar Fotovoltaica (Producción)',
    installed_capacity_kw: 1.0,
    current_power_w: 0.0,
    current_irradiance_w_m2: 0.0,
    current_t_panel_c: 0.0,
    performance_ratio: null,
    active_alerts_count: 0,
    last_updated: null
  });
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [sumData, teleData, alertsData] = await Promise.all([
        apiService.getPlantSummary('plant-01'),
        apiService.getTelemetryHistory('plant-01', 24),
        apiService.getAlerts('plant-01')
      ]);
      setSummary(sumData);
      setTelemetry(teleData);
      setAlerts(alertsData);
    } catch (err) {
      console.error("Error al consultar telemetría:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Refresco periódico cada 10 segundos
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledgeAlert = async (alertId: string) => {
    await apiService.acknowledgeAlert(alertId);
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'acknowledged' } : a));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        activeAlertsCount={alerts.filter(a => a.status === 'pending').length}
        onOpenBackdoor={() => setIsBackdoorOpen(true)}
        hasActiveTelemetry={telemetry.length > 0}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && (
          <Dashboard
            summary={summary}
            telemetry={telemetry}
            onNavigateToAlerts={() => setCurrentTab('ai')}
            onOpenBackdoor={() => setIsBackdoorOpen(true)}
          />
        )}

        {currentTab === 'monitoring' && (
          <Monitoring
            summary={summary}
            telemetry={telemetry}
          />
        )}

        {currentTab === 'ai' && (
          <AIDiagnostics />
        )}

        {currentTab === 'alerts' && (
          <AlertsPage
            alerts={alerts}
            onAcknowledge={handleAcknowledgeAlert}
            onRefresh={loadData}
          />
        )}
      </main>

      {/* Modal de Puerta Trasera (Laboratorio de Calibración / Inyección de Datos) */}
      <BackdoorModal
        isOpen={isBackdoorOpen}
        onClose={() => setIsBackdoorOpen(false)}
        onDataChanged={loadData}
      />

      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs font-mono text-slate-500">
        SystemVolt (STV) • Supervisión Industrial con Inteligencia Artificial • Sistema Real en Producción
      </footer>
    </div>
  );
};

export default App;
