"use client";

// Loaded with next/dynamic so Chart.js stays out of every other page's bundle.
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import type { VolumeProgress, WeightProgress } from "./api";

// Register only what is used (tree-shaking keeps the bundle small).
Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
);

function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

const shortDate = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("ro-RO", { day: "numeric", month: "short" });

function baseOptions(yTitle: string, showLegend: boolean) {
  const muted = token("--muted");
  const grid = token("--border");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: reduceMotion ? (false as const) : { duration: 300 },
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      // A single series needs no legend: the card title names it.
      legend: { display: showLegend, labels: { color: token("--fg"), usePointStyle: true, boxWidth: 8 } },
      tooltip: {
        backgroundColor: token("--surface-2"),
        titleColor: token("--fg"),
        bodyColor: token("--fg"),
        borderColor: grid,
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: { color: muted, maxRotation: 0, autoSkipPadding: 12 },
        grid: { display: false },
        border: { color: grid },
      },
      y: {
        title: { display: true, text: yTitle, color: muted },
        ticks: { color: muted },
        grid: { color: grid },
        border: { display: false },
      },
    },
  };
}

export function WeightChart({ data }: { data: WeightProgress }) {
  const byDate = new Map(data.entries.map((e) => [e.logged_on, Number(e.weight_kg)]));
  const weekly = new Map(data.weekly.map((w) => [w.week_start, Number(w.average_kg)]));
  const labels = [...new Set([...byDate.keys(), ...weekly.keys()])].sort();
  const options: ChartOptions<"line"> = baseOptions("kg", true);
  return (
    <Line
      aria-label="Grafic greutate: valori zilnice și media săptămânală"
      role="img"
      options={options}
      data={{
        labels: labels.map(shortDate),
        datasets: [
          {
            label: "Media săptămânală",
            data: labels.map((d) => weekly.get(d) ?? null),
            borderColor: token("--chart-1"),
            backgroundColor: token("--chart-1"),
            borderWidth: 2,
            pointRadius: 4,
            spanGaps: true,
          },
          {
            label: "Zilnic",
            data: labels.map((d) => byDate.get(d) ?? null),
            borderColor: token("--chart-2"),
            backgroundColor: token("--chart-2"),
            showLine: false,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      }}
    />
  );
}

export function VolumeChart({ data }: { data: VolumeProgress }) {
  const options: ChartOptions<"bar"> = baseOptions("kg × repetări", false);
  return (
    <Bar
      aria-label="Grafic volum săptămânal de antrenament"
      role="img"
      options={options}
      data={{
        labels: data.weekly.map((w) => shortDate(w.week_start)),
        datasets: [
          {
            label: "Volum",
            data: data.weekly.map((w) => Number(w.volume_kg)),
            backgroundColor: token("--chart-1"),
            borderRadius: 4,
            maxBarThickness: 32,
          },
        ],
      }}
    />
  );
}
