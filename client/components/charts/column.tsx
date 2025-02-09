import React from "react";
import {
  ResponsiveContainer,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDateStr } from "../../utils/date";

interface LineItem {
  stroke: string;
  dataKey: string;
}

interface Props {
  data: object[];
  xAxisDataKey: string;
  lines: LineItem[];
}

export const ColumnChart = ({ data, xAxisDataKey, lines }: Props) => {
  return (
    <div style={{ height: "400px", width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey={xAxisDataKey} tickFormatter={getDateStr} />
          <YAxis />
          <Tooltip
            labelFormatter={getDateStr}
            contentStyle={{
              color: "white",
              background: "black",
              border: "1px solid black",
            }}
          />
          <Legend />

          {lines.map((item, i) => (
            <Line
              key={i}
              type="monotone"
              dataKey={item.dataKey}
              stroke={item.stroke}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
