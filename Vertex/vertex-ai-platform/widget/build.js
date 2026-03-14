const esbuild = require("esbuild");
const path = require("path");

const isWatch = process.argv.includes("--watch");

const buildOptions = {
  entryPoints: [path.resolve(__dirname, "src/widget.ts")],
  bundle: true,
  minify: !isWatch,
  sourcemap: isWatch,
  outfile: path.resolve(__dirname, "dist/vertex-widget.js"),
  format: "iife",
  globalName: "VertexWidget",
  target: ["es2020", "chrome80", "firefox78", "safari14"],
  platform: "browser",
  define: {
    "process.env.NODE_ENV": isWatch ? '"development"' : '"production"',
  },
  banner: {
    js: "/* Vertex AI Platform — Embeddable Chat Widget v1.0.0 */",
  },
};

async function build() {
  if (isWatch) {
    const ctx = await esbuild.context(buildOptions);
    await ctx.watch();
    console.log("[vertex-widget] Watching for changes...");
  } else {
    const result = await esbuild.build(buildOptions);
    const fs = require("fs");
    const stats = fs.statSync(buildOptions.outfile);
    const kb = (stats.size / 1024).toFixed(1);
    console.log(`[vertex-widget] Built dist/vertex-widget.js (${kb} KB)`);
  }
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
