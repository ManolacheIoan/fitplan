"use client";

import dynamic from "next/dynamic";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TextField } from "@/components/ui/Field";
import { EmptyState, ErrorState, Loading } from "@/components/ui/States";
import { formatDay, nf1, todayLocal } from "@/lib/dates";
import { errorMessage } from "@/lib/errors";
import { useApi } from "@/lib/use-api";
import { Records } from "./Records";
import { deleteWeight, saveWeight, type VolumeProgress, type WeightProgress } from "./api";

const WeightChart = dynamic(() => import("./Charts").then((m) => m.WeightChart), {
  ssr: false,
  loading: () => <Loading />,
});
const VolumeChart = dynamic(() => import("./Charts").then((m) => m.VolumeChart), {
  ssr: false,
  loading: () => <Loading />,
});

// Period shown in the charts below (weeks requested from the API).
const RANGES = [
  { weeks: 4, label: "1 lună" },
  { weeks: 12, label: "3 luni" },
  { weeks: 26, label: "6 luni" },
];

function WeightForm({ onSaved }: { onSaved: (targetsUpdated: boolean) => void }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(undefined);
    try {
      const result = await saveWeight(String(form.get("date")), Number(form.get("weight")));
      onSaved(result.targets_updated);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3">
        <TextField
          label="Data"
          name="date"
          type="date"
          required
          defaultValue={todayLocal()}
          max={todayLocal()}
        />
        <TextField
          label="Greutate (kg)"
          name="weight"
          type="number"
          inputMode="decimal"
          min={30}
          max={300}
          step={0.1}
          required
        />
      </div>
      {error && (
        <p role="alert" className="text-danger text-sm font-semibold">
          {error}
        </p>
      )}
      <Button type="submit" loading={pending}>
        Salvează greutatea
      </Button>
    </form>
  );
}

function WeightTable({ data, onDeleted }: { data: WeightProgress; onDeleted: () => void }) {
  return (
    <details>
      <summary className="text-accent-text min-h-11 cursor-pointer py-2 text-sm font-semibold">
        Vezi ca tabel
      </summary>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-left">
            <th className="py-1 font-semibold">Data</th>
            <th className="py-1 font-semibold">Greutate</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {[...data.entries].reverse().map((e) => (
            <tr key={e.id} className="border-border border-t">
              <td className="py-1 capitalize">{formatDay(e.logged_on)}</td>
              <td className="py-1">{nf1.format(Number(e.weight_kg))} kg</td>
              <td className="py-1 text-right">
                <button
                  type="button"
                  className="text-danger min-h-11 px-2 font-semibold"
                  onClick={async () => {
                    await deleteWeight(e.id);
                    onDeleted();
                  }}
                >
                  Șterge
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

export function Progress() {
  const [weeks, setWeeks] = useState(12);
  const [notice, setNotice] = useState<string>();
  const weight = useApi<WeightProgress>(`/progress/weight?weeks=${weeks}`);
  const volume = useApi<VolumeProgress>(`/progress/volume?weeks=${weeks}`);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <h2 className="mb-3 text-lg font-extrabold">Greutate</h2>
        <WeightForm
          onSaved={(updated) => {
            setNotice(updated ? "Țintele au fost actualizate" : "Greutatea a fost salvată.");
            weight.reload();
          }}
        />
        {notice && (
          <p role="status" className="bg-surface-2 mt-3 rounded-xl p-3 text-sm font-semibold">
            {notice}
          </p>
        )}
      </Card>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold">Perioada afișată în grafice</legend>
        <div className="grid grid-cols-3 gap-2">
          {RANGES.map(({ weeks: w, label }) => (
            <button
              key={w}
              type="button"
              aria-pressed={weeks === w}
              onClick={() => setWeeks(w)}
              className="aria-pressed:border-accent aria-pressed:bg-accent aria-pressed:text-accent-fg border-border min-h-12 rounded-xl border text-sm font-bold"
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      <Card>
        <h2 className="mb-3 text-lg font-extrabold">Evoluția greutății</h2>
        {weight.error ? (
          <ErrorState error={weight.error} onRetry={weight.reload} />
        ) : !weight.data ? (
          <Loading />
        ) : weight.data.entries.length === 0 ? (
          <EmptyState title="Nicio greutate înregistrată în acest interval." />
        ) : (
          <>
            <div className="h-64">
              <WeightChart data={weight.data} />
            </div>
            <WeightTable data={weight.data} onDeleted={weight.reload} />
          </>
        )}
      </Card>

      <Card>
        <h2 className="mb-1 text-lg font-extrabold">Volum săptămânal</h2>
        <p className="text-muted mb-3 text-sm">Suma greutate × repetări din antrenamentele terminate.</p>
        {volume.error ? (
          <ErrorState error={volume.error} onRetry={volume.reload} />
        ) : !volume.data ? (
          <Loading />
        ) : volume.data.weekly.length === 0 ? (
          <EmptyState title="Niciun antrenament terminat în acest interval." />
        ) : (
          <>
            <div className="h-56">
              <VolumeChart data={volume.data} />
            </div>
            <details>
              <summary className="text-accent-text min-h-11 cursor-pointer py-2 text-sm font-semibold">
                Vezi ca tabel
              </summary>
              <ul className="text-sm">
                {volume.data.weekly.map((w) => (
                  <li key={w.week_start} className="border-border flex justify-between border-t py-1">
                    <span>Săptămâna din {formatDay(w.week_start)}</span>
                    <span>
                      {nf1.format(Number(w.volume_kg))} kg · {w.sessions} antr.
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          </>
        )}
      </Card>
      <Records />
    </div>
  );
}
