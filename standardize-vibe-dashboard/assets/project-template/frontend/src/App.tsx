import { Activity, Database, Moon, RefreshCw, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { getMeta, getSummary, type MetaResponse, type SummaryResponse } from "./api";
import "./index.css";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; meta: MetaResponse; summary: SummaryResponse };

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") {
    return "light";
  }

  return window.localStorage.getItem("sdu-dashboard-theme") === "dark" ? "dark" : "light";
}

export default function App() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  async function load() {
    setState({ status: "loading" });
    try {
      const [meta, summary] = await Promise.all([getMeta(), getSummary()]);
      setState({ status: "ready", meta, summary });
    } catch (error) {
      setState({ status: "error", message: error instanceof Error ? error.message : "Unknown error" });
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("sdu-dashboard-theme", theme);
  }, [theme]);

  if (state.status === "loading") {
    return <main className="shell">Загрузка данных...</main>;
  }

  if (state.status === "error") {
    return (
      <main className="shell">
        <section className="toolbar">
          <strong>Данные недоступны</strong>
          <div className="toolbar-actions">
            <button
              aria-label={theme === "dark" ? "Включить светлую тему" : "Включить тёмную тему"}
              className="icon-button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              type="button"
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button onClick={load} type="button">
              <RefreshCw size={16} />
              Обновить
            </button>
          </div>
        </section>
        <p className="error">{state.message}</p>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="toolbar">
        <div>
          <h1>Dashboard</h1>
          <p>ClickHouse: {state.meta.sourceTables.join(", ")}</p>
        </div>
        <div className="toolbar-actions">
          <button
            aria-label={theme === "dark" ? "Включить светлую тему" : "Включить тёмную тему"}
            className="icon-button secondary"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            type="button"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={load} type="button">
            <RefreshCw size={16} />
            Обновить
          </button>
        </div>
      </section>

      <section className="metrics">
        <article>
          <Database size={20} />
          <span>Таблицы</span>
          <strong>{state.summary.tableCount}</strong>
        </article>
        <article>
          <Activity size={20} />
          <span>Источники</span>
          <strong>{state.summary.sourceTables.length}</strong>
        </article>
      </section>

      <section>
        <h2>Raw tables</h2>
        <div className="table">
          <div className="row head">
            <span>name</span>
            <span>rows</span>
            <span>bytes</span>
          </div>
          {state.meta.tables.map((table) => (
            <div className="row" key={table.name}>
              <span>{table.name}</span>
              <span>{table.total_rows ?? "-"}</span>
              <span>{table.total_bytes ?? "-"}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
