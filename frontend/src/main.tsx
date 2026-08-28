import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// NOTE: removed `import "./styles.css"` — that file is leftover boilerplate
// from a different template (its own .header/.hero/.nav/.container rules
// conflict with App.css and were overriding it, since it loaded after
// App.css in the bundle). App.tsx already imports App.css directly, which
// is the actual Beauty AI stylesheet — no global import needed here.

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
