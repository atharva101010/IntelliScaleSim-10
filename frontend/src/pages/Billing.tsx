import React, { useState, useEffect } from 'react';
import { billing, Container, RealTimeBillingResponse, ScenarioSimulationResponse } from '../utils/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

type TabType = 'realtime' | 'scenario';
type Provider = 'aws' | 'gcp' | 'azure';

const Billing: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabType>('realtime');

    // Real-Time Billing State
    const [containers, setContainers] = useState<Container[]>([]);
    const [selectedContainer, setSelectedContainer] = useState<number | null>(null);
    const [provider, setProvider] = useState<Provider>('aws');
    const [timeInterval, setTimeInterval] = useState<number>(1); // hours
    const [billingData, setBillingData] = useState<RealTimeBillingResponse | null>(null);
    const [loadingBilling, setLoadingBilling] = useState(false);

    // Scenario-Based Billing State
    const [cpuCores, setCpuCores] = useState<number>(2);
    const [memoryGb, setMemoryGb] = useState<number>(4);
    const [storageGb, setStorageGb] = useState<number>(20);
    const [durationHours, setDurationHours] = useState<number>(24);
    const [scenarioProvider, setScenarioProvider] = useState<Provider>('aws');
    const [scenarioResult, setScenarioResult] = useState<ScenarioSimulationResponse | null>(null);
    const [loadingScenario, setLoadingScenario] = useState(false);

    // Load containers on mount
    useEffect(() => {
        loadContainers();
    }, []);

    const loadContainers = async () => {
        try {
            console.log('🔍 Billing: Fetching containers from API...');
            const response = await billing.getUserContainers();
            console.log('✅ Billing: Containers loaded:', response);
            setContainers(response.containers);
            if (response.containers.length > 0 && !selectedContainer) {
                setSelectedContainer(response.containers[0].id);
            }
        } catch (error: any) {
            console.error('❌ Billing: Error loading containers:', error);
            console.error('Error details:', error.message, error.response);
            // Set empty array on error so UI shows helpful message
            setContainers([]);
        }
    };

    const calculateRealTimeBilling = async () => {
        if (!selectedContainer) return;

        try {
            setLoadingBilling(true);
            const response = await billing.calculateRealTimeBilling({
                container_id: selectedContainer!,
                hours_back: timeInterval,
                provider: provider
            });

            if (response.success) {
                setBillingData(response.billing);
            }
        } catch (error: any) {
            console.error('Error calculating billing:', error);
            // If no usage data, try to collect metrics once
            if (error.message && error.message.includes('No usage data')) {
                try {
                    console.log('No data found, attempting to collect metrics...');
                    await billing.collectMetrics(selectedContainer!);
                    // Wait a second for DB to sync
                    await new Promise(resolve => setTimeout(resolve, 1500));
                    // Try again
                    const retryResponse = await billing.calculateRealTimeBilling({
                        container_id: selectedContainer!,
                        hours_back: timeInterval,
                        provider: provider
                    });
                    if (retryResponse.success) {
                        setBillingData(retryResponse.billing);
                        return;
                    }
                } catch (collectError) {
                    console.error('Failed to auto-collect metrics:', collectError);
                }
            }
            alert(`Error calculating billing: ${error.message}`);
        } finally {
            setLoadingBilling(false);
        }
    };

    const runScenarioSimulation = async () => {
        setLoadingScenario(true);
        try {
            const response = await billing.simulateScenario(
                cpuCores,
                memoryGb,
                storageGb,
                durationHours,
                scenarioProvider
            );
            setScenarioResult(response.simulation);
        } catch (error: any) {
            alert(`Error running simulation: ${error.message}`);
        } finally {
            setLoadingScenario(false);
        }
    };

    const providerColors = {
        aws: { bg: 'from-orange-500 to-yellow-500', text: 'text-orange-600' },
        gcp: { bg: 'from-blue-500 to-cyan-500', text: 'text-blue-600' },
        azure: { bg: 'from-blue-600 to-indigo-600', text: 'text-blue-700' },
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Page Header */}
                <div className="mb-8">
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
                        💰 Resource Quotas & Billing
                    </h1>
                    <p className="text-slate-600 text-lg">
                        Track costs and simulate cloud provider billing for your deployments
                    </p>
                </div>

                {/* Tab Navigation */}
                <div className="flex gap-4 mb-8">
                    <button
                        onClick={() => setActiveTab('realtime')}
                        className={`px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 ${activeTab === 'realtime'
                            ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-xl scale-105'
                            : 'bg-white text-slate-600 hover:bg-slate-100'
                            }`}
                    >
                        ⚡ Real-Time Billing
                    </button>
                    <button
                        onClick={() => setActiveTab('scenario')}
                        className={`px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 ${activeTab === 'scenario'
                            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-xl scale-105'
                            : 'bg-white text-slate-600 hover:bg-slate-100'
                            }`}
                    >
                        🎯 Scenario-Based Billing
                    </button>
                </div>

                {/* Real-Time Billing Tab */}
                {activeTab === 'realtime' && (
                    <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/60 p-10">
                        <div className="mb-8">
                            <h2 className="text-3xl font-bold text-slate-800 mb-2">Real-Time Billing Dashboard</h2>
                            <p className="text-slate-600">Track actual resource usage and associated costs</p>
                        </div>

                        {/* Configuration Controls */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                            {/* Container Selector */}
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">
                                    Select Application
                                </label>
                                <select
                                    value={selectedContainer || ''}
                                    onChange={(e) => setSelectedContainer(Number(e.target.value))}
                                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-300 bg-white text-black font-semibold focus:border-violet-500 focus:outline-none appearance-none"
                                    disabled={containers.length === 0}
                                    style={{ backgroundColor: 'white', color: 'black', opacity: 1 }}
                                >
                                    {containers.length === 0 ? (
                                        <option value="">No containers available - Deploy one first</option>
                                    ) : (
                                        <>
                                            <option value="">Select a container...</option>
                                            {containers.map((container) => (
                                                <option key={container.id} value={container.id}>
                                                    {container.name} ({container.status})
                                                </option>
                                            ))}
                                        </>
                                    )}
                                </select>
                                {containers.length === 0 && (
                                    <p className="mt-2 text-xs text-amber-600">
                                        💡 Deploy a container from the Deployments page to track billing
                                    </p>
                                )}
                            </div>

                            {/* Provider Selector */}
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">
                                    Provider Pricing Model
                                </label>
                                <div className="flex gap-2">
                                    {(['aws', 'gcp', 'azure'] as Provider[]).map((p) => (
                                        <button
                                            key={p}
                                            onClick={() => setProvider(p)}
                                            className={`flex-1 py-3 px-4 rounded-xl font-semibold uppercase transition-all ${provider === p
                                                ? `bg-gradient-to-r ${providerColors[p].bg} text-white shadow-lg`
                                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                                }`}
                                        >
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Time Interval */}
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">
                                    Time Interval
                                </label>
                                <select
                                    value={timeInterval}
                                    onChange={(e) => setTimeInterval(Number(e.target.value))}
                                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-300 bg-white text-black font-semibold focus:border-violet-500 focus:outline-none appearance-none"
                                    style={{ backgroundColor: 'white', color: 'black', opacity: 1 }}
                                >
                                    <option value={1}>Last 1 Hour</option>
                                    <option value={6}>Last 6 Hours</option>
                                    <option value={24}>Last 24 Hours</option>
                                    <option value={168}>Last 7 Days</option>
                                </select>
                            </div>
                        </div>

                        {/* Calculate Button */}
                        <button
                            onClick={calculateRealTimeBilling}
                            disabled={loadingBilling || !selectedContainer}
                            className="w-full py-4 rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 text-white font-bold text-lg shadow-xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-8"
                        >
                            {loadingBilling ? '⏳ Calculating...' : '📊 Calculate Costs'}
                        </button>

                        {/* Billing Results */}
                        {billingData && (
                            <div>
                                {/* Cost Summary Cards */}
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                                    <div className="bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl p-6 text-white">
                                        <div className="text-sm opacity-90 mb-1">CPU Cost</div>
                                        <div className="text-3xl font-bold">${billingData.costs.cpu_cost.toFixed(4)}</div>
                                    </div>
                                    <div className="bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl p-6 text-white">
                                        <div className="text-sm opacity-90 mb-1">Memory Cost</div>
                                        <div className="text-3xl font-bold">${billingData.costs.memory_cost.toFixed(4)}</div>
                                    </div>
                                    <div className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white">
                                        <div className="text-sm opacity-90 mb-1">Storage Cost</div>
                                        <div className="text-3xl font-bold">${billingData.costs.storage_cost.toFixed(4)}</div>
                                    </div>
                                    <div className="bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl p-6 text-white">
                                        <div className="text-sm opacity-90 mb-1">Total Cost</div>
                                        <div className="text-3xl font-bold">${billingData.costs.total_cost.toFixed(4)}</div>
                                    </div>
                                </div>

                                {/* Usage Graphs */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* CPU Usage */}
                                    <div className="bg-slate-50 rounded-2xl p-6">
                                        <h3 className="text-xl font-bold text-slate-800 mb-4">CPU Usage Over Time</h3>
                                        <ResponsiveContainer width="100%" height={250}>
                                            <LineChart data={billingData.usage_history}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis
                                                    dataKey="timestamp"
                                                    tickFormatter={(val: any) => new Date(val).toLocaleTimeString()}
                                                />
                                                <YAxis />
                                                <Tooltip />
                                                <Line
                                                    type="monotone"
                                                    dataKey="cpu_cores"
                                                    stroke="#8b5cf6"
                                                    strokeWidth={3}
                                                    name="CPU Cores"
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>

                                    {/* Memory Usage */}
                                    <div className="bg-slate-50 rounded-2xl p-6">
                                        <h3 className="text-xl font-bold text-slate-800 mb-4">Memory Usage Over Time</h3>
                                        <ResponsiveContainer width="100%" height={250}>
                                            <LineChart data={billingData.usage_history}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis
                                                    dataKey="timestamp"
                                                    tickFormatter={(val: any) => new Date(val).toLocaleTimeString()}
                                                />
                                                <YAxis />
                                                <Tooltip />
                                                <Line
                                                    type="monotone"
                                                    dataKey="memory_gb"
                                                    stroke="#06b6d4"
                                                    strokeWidth={3}
                                                    name="Memory (GB)"
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Cost Breakdown Details */}
                                <div className="mt-8 bg-gradient-to-br from-slate-50 to-blue-50 rounded-2xl p-6">
                                    <h3 className="text-2xl font-bold text-slate-800 mb-4">Detailed Cost Breakdown</h3>
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-slate-700">
                                                CPU: {billingData.average_usage.cpu_cores.toFixed(3)} cores × {timeInterval} hours
                                            </span>
                                            <span className="font-bold text-violet-600">
                                                ${billingData.costs.cpu_cost.toFixed(4)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-slate-700">
                                                Memory: {billingData.average_usage.memory_gb.toFixed(3)} GB × {timeInterval} hours
                                            </span>
                                            <span className="font-bold text-cyan-600">
                                                ${billingData.costs.memory_cost.toFixed(4)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-slate-700">
                                                Storage: {billingData.average_usage.storage_gb.toFixed(2)} GB
                                            </span>
                                            <span className="font-bold text-amber-600">
                                                ${billingData.costs.storage_cost.toFixed(4)}
                                            </span>
                                        </div>
                                        <div className="border-t-2 border-slate-300 pt-3 mt-3">
                                            <div className="flex justify-between items-center">
                                                <span className="text-lg font-bold text-slate-800">Total Estimated Cost</span>
                                                <span className="text-2xl font-bold text-pink-600">
                                                    ${billingData.costs.total_cost.toFixed(4)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {!billingData && !loadingBilling && (
                            <div className="text-center py-12 text-slate-500">
                                <p className="text-lg">Select a container and click "Calculate Costs" to view billing data</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Scenario-Based Billing Tab */}
                {activeTab === 'scenario' && (
                    <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/60 p-10">
                        <div className="mb-8">
                            <h2 className="text-3xl font-bold text-slate-800 mb-2">Scenario-Based Cost Simulator</h2>
                            <p className="text-slate-600">Simulate costs for hypothetical scaling scenarios</p>
                        </div>

                        {/* Resource Configuration */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                            {/* CPU Configuration */}
                            <div>
                                <label className="block text-sm font-semibold text-violet-700 mb-2">
                                    CPU Cores: {cpuCores}
                                </label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="16"
                                    step="0.5"
                                    value={cpuCores}
                                    onChange={(e) => setCpuCores(parseFloat(e.target.value))}
                                    className="w-full h-3 bg-gradient-to-r from-violet-300 to-purple-300 rounded-lg appearance-none cursor-pointer"
                                />
                                <div className="flex justify-between text-xs text-slate-500 mt-1">
                                    <span>0.5</span>
                                    <span>16 cores</span>
                                </div>
                            </div>

                            {/* Memory Configuration */}
                            <div>
                                <label className="block text-sm font-semibold text-cyan-700 mb-2">
                                    Memory: {memoryGb} GB
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="64"
                                    step="1"
                                    value={memoryGb}
                                    onChange={(e) => setMemoryGb(parseInt(e.target.value))}
                                    className="w-full h-3 bg-gradient-to-r from-cyan-300 to-blue-300 rounded-lg appearance-none cursor-pointer"
                                />
                                <div className="flex justify-between text-xs text-slate-500 mt-1">
                                    <span>1 GB</span>
                                    <span>64 GB</span>
                                </div>
                            </div>

                            {/* Storage Configuration */}
                            <div>
                                <label className="block text-sm font-semibold text-amber-700 mb-2">
                                    Storage: {storageGb} GB
                                </label>
                                <input
                                    type="range"
                                    min="10"
                                    max="1000"
                                    step="10"
                                    value={storageGb}
                                    onChange={(e) => setStorageGb(parseInt(e.target.value))}
                                    className="w-full h-3 bg-gradient-to-r from-amber-300 to-orange-300 rounded-lg appearance-none cursor-pointer"
                                />
                                <div className="flex justify-between text-xs text-slate-500 mt-1">
                                    <span>10 GB</span>
                                    <span>1000 GB</span>
                                </div>
                            </div>

                            {/* Duration Configuration */}
                            <div>
                                <label className="block text-sm font-semibold text-pink-700 mb-2">
                                    Test Duration: {durationHours} hours
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    max="720"
                                    value={durationHours}
                                    onChange={(e) => setDurationHours(parseInt(e.target.value))}
                                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-pink-500 focus:outline-none"
                                />
                            </div>
                        </div>

                        {/* Provider Selection */}
                        <div className="mb-8">
                            <label className="block text-sm font-semibold text-slate-700 mb-3">
                                Select Cloud Provider
                            </label>
                            <div className="flex gap-4">
                                {(['aws', 'gcp', 'azure'] as Provider[]).map((p) => (
                                    <button
                                        key={p}
                                        onClick={() => setScenarioProvider(p)}
                                        className={`flex-1 py-4 px-6 rounded-2xl font-bold uppercase text-lg transition-all ${scenarioProvider === p
                                            ? `bg-gradient-to-r ${providerColors[p].bg} text-white shadow-xl scale-105`
                                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                            }`}
                                    >
                                        {p}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Simulate Button */}
                        <button
                            onClick={runScenarioSimulation}
                            disabled={loadingScenario}
                            className="w-full py-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-lg shadow-xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-8"
                        >
                            {loadingScenario ? '⏳ Simulating...' : '🚀 Run Simulation'}
                        </button>

                        {/* Scenario Results */}
                        {scenarioResult && (
                            <div>
                                {/* Scenario Summary */}
                                <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-6 mb-6">
                                    <h3 className="text-2xl font-bold text-slate-800 mb-4">Scenario Configuration</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div>
                                            <div className="text-sm text-slate-600">CPU Cores</div>
                                            <div className="text-2xl font-bold text-violet-600">{scenarioResult.scenario.cpu_cores}</div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-slate-600">Memory</div>
                                            <div className="text-2xl font-bold text-cyan-600">{scenarioResult.scenario.memory_gb} GB</div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-slate-600">Storage</div>
                                            <div className="text-2xl font-bold text-amber-600">{scenarioResult.scenario.storage_gb} GB</div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-slate-600">Duration</div>
                                            <div className="text-2xl font-bold text-pink-600">{scenarioResult.scenario.duration_hours}h</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Cost Breakdown */}
                                <div className="bg-white rounded-2xl border-2 border-slate-200 p-8">
                                    <h3 className="text-2xl font-bold text-slate-800 mb-6">Cost Breakdown</h3>
                                    <div className="space-y-4">
                                        {/* CPU Cost */}
                                        <div className="p-4 bg-violet-50 rounded-xl">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-semibold text-violet-700">CPU Cost</span>
                                                <span className="text-xl font-bold text-violet-600">
                                                    ${scenarioResult.cost_breakdown.cpu.cost.toFixed(4)}
                                                </span>
                                            </div>
                                            <div className="text-sm text-slate-600">
                                                {scenarioResult.cost_breakdown.cpu.usage} @ {scenarioResult.cost_breakdown.cpu.rate}
                                            </div>
                                        </div>

                                        {/* Memory Cost */}
                                        <div className="p-4 bg-cyan-50 rounded-xl">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-semibold text-cyan-700">Memory Cost</span>
                                                <span className="text-xl font-bold text-cyan-600">
                                                    ${scenarioResult.cost_breakdown.memory.cost.toFixed(4)}
                                                </span>
                                            </div>
                                            <div className="text-sm text-slate-600">
                                                {scenarioResult.cost_breakdown.memory.usage} @ {scenarioResult.cost_breakdown.memory.rate}
                                            </div>
                                        </div>

                                        {/* Storage Cost */}
                                        <div className="p-4 bg-amber-50 rounded-xl">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="font-semibold text-amber-700">Storage Cost</span>
                                                <span className="text-xl font-bold text-amber-600">
                                                    ${scenarioResult.cost_breakdown.storage.cost.toFixed(4)}
                                                </span>
                                            </div>
                                            <div className="text-sm text-slate-600">
                                                {scenarioResult.cost_breakdown.storage.usage} @ {scenarioResult.cost_breakdown.storage.rate}
                                            </div>
                                        </div>

                                        {/* Total */}
                                        <div className="border-t-3 border-slate-300 pt-4 mt-4">
                                            <div className="flex justify-between items-center p-4 bg-gradient-to-r from-pink-50 to-rose-50 rounded-xl">
                                                <span className="text-xl font-bold text-slate-800">Total Estimated Cost</span>
                                                <span className="text-3xl font-bold text-pink-600">
                                                    ${scenarioResult.costs.total_cost.toFixed(4)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {!scenarioResult && !loadingScenario && (
                            <div className="text-center py-12 text-slate-500">
                                <p className="text-lg">Configure resources and click "Run Simulation" to see cost estimates</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Billing;
