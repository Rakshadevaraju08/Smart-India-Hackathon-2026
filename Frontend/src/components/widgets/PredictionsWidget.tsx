import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis } from 'recharts';

const data = [
  { time: '18:00', value: 2 },
  { time: '21:00', value: 5 },
  { time: '00:00', value: 3 },
  { time: '03:00', value: 10 },
  { time: '06:00', value: 22 },
  { time: '08:00', value: 16 },
  { time: '09:30', value: 27 },
  { time: '12:00', value: 11 },
  { time: '14:00', value: 6 },
  { time: '16:00', value: 15 },
  { time: '18:00', value: 13 },
  { time: '21:00', value: 7 },
  { time: '12:00', value: 2 },
];

export default function PredictionsWidget() {
  return (
    <div className="flex flex-col h-full w-full justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-[13px] font-semibold text-slate-200 tracking-wide">Active Predictions</h3>
        <span className="text-slate-400 text-lg leading-none cursor-pointer hover:text-white">...</span>
      </div>

      {/* Chart */}
      <div className="w-full h-24 mt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 8, left: -24, bottom: 0 }}>
            <defs>
              <linearGradient id="predGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00d2ff" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#00d2ff" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              ticks={['18:00', '06:00', '12:00', '18:00', '12:00']}
            />
            <YAxis
              stroke="#64748b"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              ticks={[0, 10, 20, 30]}
              tickFormatter={(val) => `${val}m`}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#00d2ff"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#predGlow)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
