// /data 산출물을 web·app의 public/data 로 복사 (빌드 전 자동 실행)
import { copyFileSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "data");
const files = readdirSync(src).filter((f) => /\.(json|geojson)$/.test(f));

for (const target of ["web", "app"]) {
  const dst = join(root, target, "public", "data");
  mkdirSync(dst, { recursive: true });
  for (const f of files) copyFileSync(join(src, f), join(dst, f));
  console.log(`${target}/public/data <- ${files.join(", ")}`);
}
