import imageMap from "../data/images.json";

const metaModules = import.meta.glob("../data/notes/*.meta.json", { eager: true });
const mdModules = import.meta.glob("../data/notes/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
});

const SECTION_IDS_ORDER = ["m1_l1", "m1_l2", "m2_l1", "m2_l2", "m3_l1", "m3_l2", "midterm"];

function buildSectionMap(modules, suffix) {
  const map = {};
  for (const [path, mod] of Object.entries(modules)) {
    const fileName = path.split("/").pop();
    const sectionId = fileName.replace(suffix, "");
    map[sectionId] = mod.default ?? mod;
  }
  return map;
}

const metaMap = buildSectionMap(metaModules, ".meta.json");
const mdMap = buildSectionMap(mdModules, ".md");

export function getNote(sectionId) {
  const meta = metaMap[sectionId];
  const md = mdMap[sectionId];
  if (!meta || !md) return null;

  return {
    sectionId,
    title: meta.title,
    markdown: md,
    prompt: meta.prompt_preview || meta.prompt || "",
    sources: meta.sources || [],
    chunksUsed: meta.chunks_used || 0,
    contextChars: meta.context_chars || 0,
    images: imageMap[sectionId] || [],
  };
}

export function listNotes() {
  return SECTION_IDS_ORDER
    .filter((id) => metaMap[id] && mdMap[id])
    .map((id) => ({
      sectionId: id,
      title: metaMap[id].title,
    }));
}

export function getSectionImages(sectionId, type) {
  const images = imageMap[sectionId] || [];
  if (type) return images.filter((img) => img.type === type);
  return images;
}
