import imageMap from "../data/images.json";

const metaModules = import.meta.glob("../data/notes/*.meta.json", {
  eager: true,
});
const mdModules = import.meta.glob("../data/notes/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
});

const SECTION_IDS_ORDER = [
  "m1_l1",
  "m1_l2",
  "m2_l1",
  "m2_l2",
  "m3_l1",
  "m3_l2",
  "m4_l1",
  "m4_l2",
  "m5_l1",
  "m5_l2",
  "midterm",
];

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
  return SECTION_IDS_ORDER.filter((id) => metaMap[id] && mdMap[id]).map(
    (id) => ({
      sectionId: id,
      title: metaMap[id].title,
    }),
  );
}

export function getSectionImages(sectionId, type) {
  const images = imageMap[sectionId] || [];
  if (type) return images.filter((img) => img.type === type);
  return images;
}

// Slide-page renders generated from the source .pptx via LibreOffice → PDF →
// pdftoppm. One PNG per slide page, named `${sectionId}_slide-NN.png` and
// stored under public/cog-neuro/slides/. These are the full PowerPoint slide
// pages (vs. the extracted-figure thumbnails in images.json).
const SLIDE_PAGE_COUNTS = {
  m1_l1: 32,
  m1_l2: 36,
  m2_l1: 27,
  m3_l1: 32,
  m4_l1: 30,
  m4_l2: 35,
  m5_l1: 29,
  m5_l2: 32,
};

export function getSlidePages(sectionId) {
  const count = SLIDE_PAGE_COUNTS[sectionId];
  if (!count) return [];
  return Array.from({ length: count }, (_, i) => {
    const num = i + 1;
    const padded = String(num).padStart(2, "0");
    return {
      slide: num,
      url: `/cog-neuro/slides/${sectionId}_slide-${padded}.png`,
      caption: `Slide ${num}`,
      type: "slide-page",
    };
  });
}
