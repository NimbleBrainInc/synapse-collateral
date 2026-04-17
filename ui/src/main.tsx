import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { SynapseProvider } from "@nimblebrain/synapse/react";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <SynapseProvider name="synapse-collateral" version="0.3.3">
      <App />
    </SynapseProvider>
  </StrictMode>,
);
