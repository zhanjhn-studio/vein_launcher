/* Command candidate tree (English labels)
 *
 * key      — normalized command prefix (no leading "/", runs of spaces collapsed)
 * candidate — token appended to the input box when clicked
 *
 * Targets Java Edition 1.13+ syntax; the world needs cheats enabled or OP.
 */

export interface Candidate {
  /** Text appended on click (numbers/coords ship a usable default) */
  token: string;
  /** Optional explicit English label; falls back to label(token) */
  hint?: string;
  /** Optional section title, used only by the initial list */
  group?: string;
}

export interface CommandNode {
  candidates: Candidate[];
}

/** 带上级路径的候选，用于跨层级检索 */
export interface IndexedCandidate extends Candidate {
  parent: string;
}

/** 少量需要人话的 token（选择器、布尔、游戏模式等），其余走通用规则 */
const SPECIAL_LABELS: Record<string, string> = {
  '@s': 'Self',
  '@a': 'All players',
  '@p': 'Nearest player',
  '@r': 'Random player',
  '@e': 'All entities',
  true: 'On',
  false: 'Off',
  survival: 'Survival mode',
  creative: 'Creative mode',
  adventure: 'Adventure mode',
  spectator: 'Spectator mode',
  clear: 'Clear',
  rain: 'Rain',
  thunder: 'Thunder',
  day: 'Day',
  noon: 'Noon',
  night: 'Night',
  midnight: 'Midnight',
  keep: 'Keep items on death',
  dummy: 'Scoreboard objective',
  // 常用指令：避免直译成 Gamemode / Tp 这种生硬写法
  gamemode: 'Game mode',
  defaultgamemode: 'Default game mode',
  difficulty: 'Difficulty',
  tp: 'Teleport',
  teleport: 'Teleport',
  kill: 'Kill entities',
  effect: 'Status effect',
  enchant: 'Enchant item',
  xp: 'Experience',
  experience: 'Experience',
  give: 'Give item',
  summon: 'Summon entity',
  setblock: 'Set block',
  fill: 'Fill region',
  clone: 'Clone region',
  execute: 'Execute (chained)',
  gamerule: 'Game rule',
  time: 'Time of day',
  weather: 'Weather',
  say: 'Say in chat',
  tell: 'Private message',
  msg: 'Private message',
  tellraw: 'Raw JSON message',
  playsound: 'Play sound',
  particle: 'Particle effect',
  tag: 'Entity tags',
  team: 'Teams',
  scoreboard: 'Scoreboard',
  objectives: 'Scoreboard objectives',
  function: 'Datapack function',
  datapack: 'Datapack',
  reload: 'Reload datapacks',
  seed: 'World seed',
  spawnpoint: 'Spawn point',
  setworldspawn: 'World spawn',
  locate: 'Locate structure',
  list: 'List players',
  op: 'Grant operator',
  deop: 'Revoke operator',
  kick: 'Kick player',
  whitelist: 'Whitelist',
  stop: 'Stop server',
  save: 'Save world',
  advance: 'Advancement',
  recipe: 'Recipe',
  attribute: 'Attribute',
  data: 'NBT data',
  item: 'Item stack',
  loot: 'Loot table',
  place: 'Place feature',
  ride: 'Ride entity',
  spectate: 'Spectate',
  spreadplayers: 'Spread players',
  worldborder: 'World border',
  bossbar: 'Boss bar',
  camera: 'Camera',
  me: 'Emote',
};

function titleCase(value: string): string {
  return value
    .split(/[_\s./:]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/** token → 英文说明（数据里不再存中文 hint，统一在这里生成） */
export function label(token: string): string {
  const key = token.trim();
  if (!key) return '';

  const special = SPECIAL_LABELS[key];
  if (special) return special;

  const placeholder = /^<([^>]+)>$/.exec(key);
  if (placeholder) return titleCase(placeholder[1]);

  if (key.startsWith('@')) return 'Entity selector';
  if (/^[~^]/.test(key)) return 'Coordinates';
  if (/^-?\d/.test(key)) return 'Number';
  if (key.startsWith('{') || key.includes('{')) return 'NBT data';
  if (key.startsWith('#') || key.includes('[')) return 'Item predicate';

  return titleCase(key.replace(/^minecraft:/, ''));
}

/** 优先用显式 hint，否则由 token 生成 */
export function displayHint(candidate: Candidate): string {
  return candidate.hint ?? label(candidate.token);
}

const TARGETS: Candidate[] = [
  { token: '@s' },
  { token: '@a' },
  { token: '@p' },
  { token: '@r' },
  { token: '<player>' },
];

const SELECTORS: Candidate[] = [
  { token: '@e' },
  { token: '@a' },
  { token: '@p' },
  { token: '@r' },
  { token: '@s' },
  { token: '<player>' },
];

const BOOL: Candidate[] = [
  { token: 'true' },
  { token: 'false' },
];

/** 物品表：按"常用度 + 分类"排，hint 全部中文，可被中文检索 */
const ITEMS: Candidate[] = [
  // ---------------- 方块
  { token: 'minecraft:stone' },
  { token: 'minecraft:cobblestone' },
  { token: 'minecraft:dirt' },
  { token: 'minecraft:grass_block' },
  { token: 'minecraft:sand' },
  { token: 'minecraft:gravel' },
  { token: 'minecraft:oak_log' },
  { token: 'minecraft:oak_planks' },
  { token: 'minecraft:glass' },
  { token: 'minecraft:bricks' },
  { token: 'minecraft:obsidian' },
  { token: 'minecraft:netherrack' },
  { token: 'minecraft:end_stone' },
  { token: 'minecraft:sandstone' },
  { token: 'minecraft:deepslate' },
  { token: 'minecraft:iron_block' },
  { token: 'minecraft:gold_block' },
  { token: 'minecraft:diamond_block' },
  { token: 'minecraft:emerald_block' },
  { token: 'minecraft:netherite_block' },
  { token: 'minecraft:coal_block' },
  { token: 'minecraft:redstone_block' },
  { token: 'minecraft:quartz_block' },
  { token: 'minecraft:glowstone' },
  { token: 'minecraft:sea_lantern' },
  { token: 'minecraft:torch' },
  { token: 'minecraft:ladder' },
  { token: 'minecraft:chest' },
  { token: 'minecraft:furnace' },
  { token: 'minecraft:crafting_table' },
  { token: 'minecraft:anvil' },
  { token: 'minecraft:enchanting_table' },
  { token: 'minecraft:beacon' },
  { token: 'minecraft:hopper' },
  { token: 'minecraft:ender_chest' },
  { token: 'minecraft:shulker_box' },
  { token: 'minecraft:tnt' },
  { token: 'minecraft:scaffolding' },
  { token: 'minecraft:lightning_rod' },
  { token: 'minecraft:target' },
  { token: 'minecraft:note_block' },
  { token: 'minecraft:jukebox' },
  { token: 'minecraft:conduit' },
  { token: 'minecraft:amethyst_block' },
  { token: 'minecraft:copper_block' },

  // ---------------- 工具 / 武器 / 盔甲
  { token: 'minecraft:iron_sword' },
  { token: 'minecraft:diamond_sword' },
  { token: 'minecraft:netherite_sword' },
  { token: 'minecraft:stone_sword' },
  { token: 'minecraft:wooden_sword' },
  { token: 'minecraft:bow' },
  { token: 'minecraft:crossbow' },
  { token: 'minecraft:arrow' },
  { token: 'minecraft:spectral_arrow' },
  { token: 'minecraft:trident' },
  { token: 'minecraft:shield' },
  { token: 'minecraft:iron_pickaxe' },
  { token: 'minecraft:diamond_pickaxe' },
  { token: 'minecraft:netherite_pickaxe' },
  { token: 'minecraft:iron_axe' },
  { token: 'minecraft:diamond_axe' },
  { token: 'minecraft:iron_shovel' },
  { token: 'minecraft:fishing_rod' },
  { token: 'minecraft:flint_and_steel' },
  { token: 'minecraft:shears' },
  { token: 'minecraft:elytra' },
  { token: 'minecraft:iron_helmet' },
  { token: 'minecraft:iron_chestplate' },
  { token: 'minecraft:iron_leggings' },
  { token: 'minecraft:iron_boots' },
  { token: 'minecraft:diamond_helmet' },
  { token: 'minecraft:diamond_chestplate' },
  { token: 'minecraft:diamond_leggings' },
  { token: 'minecraft:diamond_boots' },
  { token: 'minecraft:netherite_chestplate' },
  { token: 'minecraft:turtle_helmet' },
  { token: 'minecraft:carrot_on_a_stick' },

  // ---------------- 食物
  { token: 'minecraft:apple' },
  { token: 'minecraft:golden_apple' },
  { token: 'minecraft:enchanted_golden_apple' },
  { token: 'minecraft:bread' },
  { token: 'minecraft:cooked_beef' },
  { token: 'minecraft:cooked_porkchop' },
  { token: 'minecraft:cooked_chicken' },
  { token: 'minecraft:golden_carrot' },
  { token: 'minecraft:carrot' },
  { token: 'minecraft:potato' },
  { token: 'minecraft:baked_potato' },
  { token: 'minecraft:melon_slice' },
  { token: 'minecraft:cookie' },
  { token: 'minecraft:cake' },
  { token: 'minecraft:pumpkin_pie' },
  { token: 'minecraft:sweet_berries' },
  { token: 'minecraft:honey_bottle' },

  // ---------------- 材料
  { token: 'minecraft:stick' },
  { token: 'minecraft:coal' },
  { token: 'minecraft:charcoal' },
  { token: 'minecraft:iron_ingot' },
  { token: 'minecraft:gold_ingot' },
  { token: 'minecraft:copper_ingot' },
  { token: 'minecraft:diamond' },
  { token: 'minecraft:emerald' },
  { token: 'minecraft:netherite_ingot' },
  { token: 'minecraft:netherite_scrap' },
  { token: 'minecraft:lapis_lazuli' },
  { token: 'minecraft:redstone' },
  { token: 'minecraft:quartz' },
  { token: 'minecraft:amethyst_shard' },
  { token: 'minecraft:string' },
  { token: 'minecraft:leather' },
  { token: 'minecraft:feather' },
  { token: 'minecraft:flint' },
  { token: 'minecraft:gunpowder' },
  { token: 'minecraft:blaze_rod' },
  { token: 'minecraft:blaze_powder' },
  { token: 'minecraft:ender_pearl' },
  { token: 'minecraft:ender_eye' },
  { token: 'minecraft:slime_ball' },
  { token: 'minecraft:ghast_tear' },
  { token: 'minecraft:nether_star' },
  { token: 'minecraft:totem_of_undying' },
  { token: 'minecraft:ink_sac' },
  { token: 'minecraft:glow_ink_sac' },
  { token: 'minecraft:bone' },
  { token: 'minecraft:bone_meal' },
  { token: 'minecraft:sugar' },
  { token: 'minecraft:paper' },
  { token: 'minecraft:book' },
  { token: 'minecraft:enchanted_book' },
  { token: 'minecraft:writable_book' },
  { token: 'minecraft:name_tag' },
  { token: 'minecraft:saddle' },
  { token: 'minecraft:dragon_breath' },
  { token: 'minecraft:experience_bottle' },
  { token: 'minecraft:glass_bottle' },

  // ---------------- 红石 / 载具 / 杂项
  { token: 'minecraft:redstone_torch' },
  { token: 'minecraft:repeater' },
  { token: 'minecraft:comparator' },
  { token: 'minecraft:piston' },
  { token: 'minecraft:sticky_piston' },
  { token: 'minecraft:observer' },
  { token: 'minecraft:dispenser' },
  { token: 'minecraft:dropper' },
  { token: 'minecraft:rail' },
  { token: 'minecraft:powered_rail' },
  { token: 'minecraft:minecart' },
  { token: 'minecraft:bucket' },
  { token: 'minecraft:water_bucket' },
  { token: 'minecraft:lava_bucket' },
  { token: 'minecraft:milk_bucket' },
  { token: 'minecraft:item_frame' },
  { token: 'minecraft:armor_stand' },
  { token: 'minecraft:painting' },
  { token: 'minecraft:compass' },
  { token: 'minecraft:clock' },
  { token: 'minecraft:map' },
  { token: 'minecraft:spyglass' },
  { token: 'minecraft:recovery_compass' },
  { token: 'minecraft:lodestone' },
  { token: 'minecraft:end_crystal' },
  { token: 'minecraft:firework_rocket' },
];

const EFFECTS: Candidate[] = [
  { token: 'minecraft:regeneration' },
  { token: 'minecraft:speed' },
  { token: 'minecraft:strength' },
  { token: 'minecraft:night_vision' },
  { token: 'minecraft:fire_resistance' },
  { token: 'minecraft:water_breathing' },
  { token: 'minecraft:absorption' },
  { token: 'minecraft:invisibility' },
  { token: 'minecraft:jump_boost' },
  { token: 'minecraft:haste' },
  { token: 'minecraft:luck' },
];

const ENTITIES: Candidate[] = [
  { token: 'minecraft:zombie' },
  { token: 'minecraft:skeleton' },
  { token: 'minecraft:creeper' },
  { token: 'minecraft:spider' },
  { token: 'minecraft:enderman' },
  { token: 'minecraft:villager' },
  { token: 'minecraft:cow' },
  { token: 'minecraft:pig' },
  { token: 'minecraft:sheep' },
  { token: 'minecraft:chicken' },
  { token: 'minecraft:horse' },
  { token: 'minecraft:wolf' },
  { token: 'minecraft:iron_golem' },
];

const GAMEMODES: Candidate[] = [
  { token: 'survival' },
  { token: 'creative' },
  { token: 'adventure' },
  { token: 'spectator' },
];

const TIME_VALUES: Candidate[] = [
  { token: 'day' },
  { token: 'noon' },
  { token: 'night' },
  { token: 'midnight' },
  { token: '1000' },
];

const GAMERULES: Candidate[] = [
  { token: 'keepInventory' },
  { token: 'doDaylightCycle' },
  { token: 'doMobSpawning' },
  { token: 'doFireTick' },
  { token: 'mobGriefing' },
  { token: 'showCoordinates' },
];

/** 指令总表：覆盖 Java 版 1.21 的全部指令（来源：minecraft.wiki/w/Commands） */
export const ROOT_CANDIDATES: Candidate[] = [
  // ---------------- Basics
  { token: 'gamemode', group: 'Basics' },
  { token: 'defaultgamemode', group: 'Basics' },
  { token: 'difficulty', group: 'Basics' },
  { token: 'tp', group: 'Basics' },
  { token: 'teleport', group: 'Basics' },
  { token: 'kill', group: 'Basics' },
  { token: 'clear', group: 'Basics' },
  { token: 'effect', group: 'Basics' },
  { token: 'enchant', group: 'Basics' },
  { token: 'xp', group: 'Basics' },
  { token: 'experience', group: 'Basics' },
  { token: 'give', group: 'Basics' },
  { token: 'item', group: 'Basics' },
  { token: 'recipe', group: 'Basics' },
  { token: 'advancement', group: 'Basics' },
  { token: 'spawnpoint', group: 'Basics' },
  { token: 'setworldspawn', group: 'Basics' },

  // ---------------- World & Blocks
  { token: 'time', group: 'World & Blocks' },
  { token: 'weather', group: 'World & Blocks' },
  { token: 'gamerule', group: 'World & Blocks' },
  { token: 'setblock', group: 'World & Blocks' },
  { token: 'fill', group: 'World & Blocks' },
  { token: 'clone', group: 'World & Blocks' },
  { token: 'fillbiome', group: 'World & Blocks' },
  { token: 'place', group: 'World & Blocks' },
  { token: 'locate', group: 'World & Blocks' },
  { token: 'forceload', group: 'World & Blocks' },
  { token: 'worldborder', group: 'World & Blocks' },
  { token: 'seed', group: 'World & Blocks' },

  // ---------------- Entities & Status
  { token: 'summon', group: 'Entities & Status' },
  { token: 'attribute', group: 'Entities & Status' },
  { token: 'damage', group: 'Entities & Status' },
  { token: 'ride', group: 'Entities & Status' },
  { token: 'rotate', group: 'Entities & Status' },
  { token: 'spectate', group: 'Entities & Status' },
  { token: 'tag', group: 'Entities & Status' },
  { token: 'team', group: 'Entities & Status' },
  { token: 'teammsg', group: 'Entities & Status' },
  { token: 'spreadplayers', group: 'Entities & Status' },
  { token: 'loot', group: 'Entities & Status' },
  { token: 'particle', group: 'Entities & Status' },
  { token: 'playsound', group: 'Entities & Status' },
  { token: 'stopsound', group: 'Entities & Status' },
  { token: 'posteffect', group: 'Entities & Status' },

  // ---------------- Messages & Display
  { token: 'say', group: 'Messages & Display' },
  { token: 'me', group: 'Messages & Display' },
  { token: 'tell', group: 'Messages & Display' },
  { token: 'msg', group: 'Messages & Display' },
  { token: 'tellraw', group: 'Messages & Display' },
  { token: 'title', group: 'Messages & Display' },
  { token: 'bossbar', group: 'Messages & Display' },
  { token: 'dialog', group: 'Messages & Display' },

  // ---------------- Logic & Data
  { token: 'execute', group: 'Logic & Data' },
  { token: 'function', group: 'Logic & Data' },
  { token: 'schedule', group: 'Logic & Data' },
  { token: 'datapack', group: 'Logic & Data' },
  { token: 'reload', group: 'Logic & Data' },
  { token: 'data', group: 'Logic & Data' },
  { token: 'scoreboard', group: 'Logic & Data' },
  { token: 'random', group: 'Logic & Data' },
  { token: 'return', group: 'Logic & Data' },
  { token: 'tick', group: 'Logic & Data' },
  { token: 'stopwatch', group: 'Logic & Data' },
  { token: 'test', group: 'Logic & Data' },
  { token: 'compute', group: 'Logic & Data' },

  // ---------------- Server Admin
  { token: 'list', group: 'Server Admin' },
  { token: 'help', group: 'Server Admin' },
  { token: 'op', group: 'Server Admin' },
  { token: 'deop', group: 'Server Admin' },
  { token: 'kick', group: 'Server Admin' },
  { token: 'ban', group: 'Server Admin' },
  { token: 'ban-ip', group: 'Server Admin' },
  { token: 'banlist', group: 'Server Admin' },
  { token: 'pardon', group: 'Server Admin' },
  { token: 'pardon-ip', group: 'Server Admin' },
  { token: 'whitelist', group: 'Server Admin' },
  { token: 'save-all', group: 'Server Admin' },
  { token: 'save-off', group: 'Server Admin' },
  { token: 'save-on', group: 'Server Admin' },
  { token: 'stop', group: 'Server Admin' },
  { token: 'setidletimeout', group: 'Server Admin' },
  { token: 'publish', group: 'Server Admin' },
  { token: 'transfer', group: 'Server Admin' },
  { token: 'version', group: 'Server Admin' },

  // ---------------- Debug
  { token: 'perf', group: 'Debug' },
  { token: 'jfr', group: 'Debug' },
  { token: 'debug', group: 'Debug' },
  { token: 'fetchprofile', group: 'Debug' },
];

export const COMMAND_TREE: Record<string, CommandNode> = {
  // ---------------------------------------------------------------- gamemode
  gamemode: { candidates: GAMEMODES },
  'gamemode survival': { candidates: TARGETS },
  'gamemode creative': { candidates: TARGETS },
  'gamemode adventure': { candidates: TARGETS },
  'gamemode spectator': { candidates: TARGETS },

  // ---------------------------------------------------------------- kill
  kill: { candidates: SELECTORS },
  'kill @e': {
    candidates: [
      { token: '[type=!player]' },
      { token: '[type=minecraft:zombie]' },
      { token: '[distance=..10]' },
      { token: '[limit=1]' },
      { token: '[sort=nearest]' },
    ],
  },
  'kill @a': {
    candidates: [
      { token: '[limit=1]' },
      { token: '[distance=..5]' },
    ],
  },
  'kill @p': { candidates: [] },
  'kill @r': { candidates: [] },
  'kill @s': { candidates: [] },

  // ---------------------------------------------------------------- tp
  tp: { candidates: TARGETS },
  'tp @s': {
    candidates: [
      { token: '0 100 0' },
      { token: '~ ~ ~' },
      { token: '~ ~1 ~' },
      { token: '@p' },
    ],
  },
  'tp @a': { candidates: [{ token: '0 100 0' }] },

  // ---------------------------------------------------------------- give
  give: { candidates: TARGETS },
  'give @s': { candidates: ITEMS },
  'give @a': { candidates: ITEMS },
  'give @p': { candidates: ITEMS },

  // ---------------------------------------------------------------- effect
  effect: {
    candidates: [
      { token: 'give' },
      { token: 'clear' },
    ],
  },
  'effect give': { candidates: TARGETS },
  'effect clear': { candidates: TARGETS },
  'effect give @s': { candidates: EFFECTS },
  'effect give @a': { candidates: EFFECTS },

  // ---------------------------------------------------------------- time
  time: {
    candidates: [
      { token: 'set' },
      { token: 'add' },
      { token: 'query' },
    ],
  },
  'time set': { candidates: TIME_VALUES },
  'time add': {
    candidates: [
      { token: '1000' },
      { token: '-1000' },
    ],
  },
  'time query': {
    candidates: [
      { token: 'daytime' },
      { token: 'day' },
    ],
  },

  // ---------------------------------------------------------------- weather
  weather: {
    candidates: [
      { token: 'clear' },
      { token: 'rain' },
      { token: 'thunder' },
    ],
  },
  'weather clear': { candidates: [{ token: '6000' }] },
  'weather rain': { candidates: [{ token: '6000' }] },
  'weather thunder': { candidates: [{ token: '6000' }] },

  // ---------------------------------------------------------------- gamerule
  gamerule: { candidates: GAMERULES },
  'gamerule keepInventory': { candidates: BOOL },
  'gamerule doDaylightCycle': { candidates: BOOL },
  'gamerule doMobSpawning': { candidates: BOOL },
  'gamerule doFireTick': { candidates: BOOL },
  'gamerule mobGriefing': { candidates: BOOL },
  'gamerule showCoordinates': { candidates: BOOL },

  // ---------------------------------------------------------------- 其他
  clear: { candidates: TARGETS },
  spawnpoint: { candidates: TARGETS },
  'spawnpoint @s': {
    candidates: [
      { token: '~ ~ ~' },
      { token: '0 64 0' },
    ],
  },
  summon: { candidates: ENTITIES },
  enchant: { candidates: TARGETS },
  'enchant @s': {
    candidates: [
      { token: 'minecraft:sharpness' },
      { token: 'minecraft:protection' },
      { token: 'minecraft:unbreaking' },
      { token: 'minecraft:efficiency' },
      { token: 'minecraft:fortune' },
      { token: 'minecraft:power' },
    ],
  },

  // ---------------------------------------------------------------- xp / 方块操作
  xp: {
    candidates: [
      { token: 'add' },
      { token: 'set' },
      { token: 'query' },
    ],
  },
  'xp add': { candidates: TARGETS },
  'xp add @s': {
    candidates: [
      { token: '30 levels' },
      { token: '100 points' },
    ],
  },
  setblock: { candidates: [{ token: '0 64 0' }] },
  'setblock 0 64 0': { candidates: ITEMS.slice(0, 20) },
  fill: { candidates: [{ token: '0 64 0 10 70 10' }] },
  'fill 0 64 0 10 70 10': { candidates: ITEMS.slice(0, 20) },
  locate: {
    candidates: [
      { token: 'structure village' },
      { token: 'structure fortress' },
      { token: 'structure stronghold' },
      { token: 'biome plains' },
    ],
  },
  playsound: {
    candidates: [
      { token: 'minecraft:entity.player.levelup' },
      { token: 'minecraft:entity.experience_orb.pickup' },
      { token: 'minecraft:block.note_block.harp' },
    ],
  },
  difficulty: {
    candidates: [
      { token: 'peaceful' },
      { token: 'easy' },
      { token: 'normal' },
      { token: 'hard' },
    ],
  },
  seed: { candidates: [] },
  list: { candidates: [] },

  // ================================================================ 1.21 全量指令分支
  defaultgamemode: { candidates: GAMEMODES },
  teleport: { candidates: TARGETS },
  'teleport @s': {
    candidates: [
      { token: '0 100 0' },
      { token: '~ ~1 ~' },
      { token: '@p' },
    ],
  },

  advancement: {
    candidates: [
      { token: 'grant' },
      { token: 'revoke' },
    ],
  },
  'advancement grant': { candidates: TARGETS },
  'advancement grant @s': {
    candidates: [
      { token: 'everything' },
      { token: 'only minecraft:story/root' },
      { token: 'from minecraft:story/root' },
    ],
  },
  'advancement revoke': { candidates: TARGETS },
  'advancement revoke @s': { candidates: [{ token: 'everything' }] },

  item: {
    candidates: [
      { token: 'replace' },
      { token: 'modify' },
    ],
  },
  'item replace': { candidates: TARGETS },
  'item replace entity @s': {
    candidates: [
      { token: 'weapon.mainhand' },
      { token: 'weapon.offhand' },
      { token: 'armor.head' },
      { token: 'inventory.0' },
    ],
  },
  'item replace entity @s weapon.mainhand': {
    candidates: [
      { token: 'with minecraft:diamond_sword' },
      { token: 'with minecraft:golden_apple 16' },
    ],
  },

  recipe: {
    candidates: [
      { token: 'give' },
      { token: 'take' },
    ],
  },
  'recipe give': { candidates: TARGETS },
  'recipe give @s': { candidates: [{ token: '*' }] },

  clone: { candidates: [{ token: '0 64 0 5 70 5 10 64 0' }] },
  'clone 0 64 0 5 70 5 10 64 0': {
    candidates: [
      { token: 'replace' },
      { token: 'masked' },
      { token: 'force' },
    ],
  },

  fillbiome: { candidates: [{ token: '0 64 0 10 70 10 minecraft:plains' }] },

  place: {
    candidates: [
      { token: 'feature minecraft:oak' },
      { token: 'structure minecraft:village_plains' },
      { token: 'jigsaw minecraft:village/plains/houses/plains_small_house_1' },
      { token: 'template minecraft:village/plains/houses/plains_small_house_1' },
    ],
  },

  forceload: {
    candidates: [
      { token: 'add' },
      { token: 'remove' },
      { token: 'query' },
    ],
  },
  'forceload add': { candidates: [{ token: '0 0' }] },

  worldborder: {
    candidates: [
      { token: 'set' },
      { token: 'center' },
      { token: 'add' },
      { token: 'damage' },
      { token: 'get' },
    ],
  },
  'worldborder set': { candidates: [{ token: '100' }] },
  'worldborder center': { candidates: [{ token: '0 0' }] },
  'worldborder damage': {
    candidates: [
      { token: 'amount 1' },
      { token: 'buffer 5' },
    ],
  },

  setworldspawn: { candidates: [{ token: '0 64 0' }] },

  attribute: { candidates: TARGETS },
  'attribute @s': {
    candidates: [
      { token: 'minecraft:generic.max_health get' },
      { token: 'minecraft:generic.movement_speed get' },
      { token: 'minecraft:generic.attack_damage base set 100' },
    ],
  },

  damage: { candidates: TARGETS },
  'damage @s': { candidates: [{ token: '10' }] },
  'damage @e[type=!player]': { candidates: [{ token: '5' }] },

  ride: { candidates: TARGETS },
  'ride @s': {
    candidates: [
      { token: 'mount @p' },
      { token: 'dismount' },
    ],
  },
  rotate: { candidates: TARGETS },
  'rotate @s': { candidates: [{ token: '90 0' }] },
  spectate: { candidates: TARGETS },

  tag: { candidates: TARGETS },
  'tag @s': {
    candidates: [
      { token: 'add test' },
      { token: 'remove test' },
      { token: 'list' },
    ],
  },
  team: {
    candidates: [
      { token: 'add red_team' },
      { token: 'list' },
      { token: 'join red_team' },
      { token: 'leave red_team' },
      { token: 'remove red_team' },
    ],
  },
  'team join': { candidates: TARGETS },
  teammsg: { candidates: [{ token: 'Hello everyone' }] },

  spreadplayers: {
    candidates: [{ token: '0 0 10 10 false @a' }],
  },

  loot: {
    candidates: [
      { token: 'give @s minecraft:chests/simple_dungeon' },
      { token: 'spawn 0 64 0 minecraft:chests/simple_dungeon' },
      { token: 'insert 0 64 0 minecraft:chests/simple_dungeon' },
    ],
  },

  particle: {
    candidates: [
      { token: 'minecraft:flame ~ ~1 ~ 0 0 0 0 20' },
      { token: 'minecraft:heart ~ ~1 ~ 0 0 0 0 10' },
      { token: 'minecraft:happy_villager ~ ~1 ~ 0 0 0 0 30' },
      { token: 'minecraft:explosion ~ ~1 ~ 0 0 0 0 5' },
    ],
  },

  stopsound: { candidates: TARGETS },
  posteffect: {
    candidates: [
      { token: 'give @s minecraft:invert' },
      { token: 'give @s minecraft:notch' },
      { token: 'clear @s' },
    ],
  },

  say: { candidates: [] },
  me: { candidates: [] },
  tell: { candidates: TARGETS },
  msg: { candidates: TARGETS },
  tellraw: { candidates: TARGETS },
  'tellraw @a': { candidates: [{ token: '{"text":"Hello"}' }] },
  title: { candidates: TARGETS },
  'title @a': {
    candidates: [
      { token: 'title Welcome' },
      { token: 'subtitle <subtitle>' },
      { token: 'actionbar <message>' },
      { token: 'times 10 70 20' },
      { token: 'clear' },
    ],
  },
  bossbar: {
    candidates: [
      { token: 'add minecraft:custom <name>' },
      { token: 'remove minecraft:custom' },
      { token: 'list' },
      { token: 'set minecraft:custom value 50' },
    ],
  },
  dialog: {
    candidates: [
      { token: 'show @a minecraft:server_links' },
      { token: 'clear @a' },
    ],
  },

  execute: {
    candidates: [
      { token: 'as @a at @s run tp ~ ~1 ~' },
      { token: 'if entity @a run say someone is online' },
      { token: 'positioned 0 64 0 run setblock ~ ~ ~ minecraft:stone' },
    ],
  },
  function: { candidates: [{ token: 'minecraft:test' }] },
  schedule: {
    candidates: [
      { token: 'function minecraft:test 10s' },
      { token: 'function minecraft:test 5t' },
      { token: 'clear minecraft:test' },
    ],
  },
  datapack: {
    candidates: [
      { token: 'list' },
      { token: 'enable <pack>' },
      { token: 'disable <pack>' },
    ],
  },
  reload: { candidates: [] },
  data: {
    candidates: [
      { token: 'get entity @s' },
      { token: 'get block 0 64 0' },
      { token: 'get storage minecraft:test' },
      { token: 'merge entity @s {"Tags":["test"]}' },
    ],
  },
  scoreboard: {
    candidates: [
      { token: 'objectives add score dummy' },
      { token: 'objectives list' },
      { token: 'players set @s score 100' },
      { token: 'players list @s' },
    ],
  },
  random: {
    candidates: [
      { token: 'value 1..6' },
      { token: 'reset *' },
    ],
  },
  return: { candidates: [{ token: '1' }] },
  tick: {
    candidates: [
      { token: 'freeze' },
      { token: 'unfreeze' },
      { token: 'step 1' },
      { token: 'rate 20' },
      { token: 'query' },
    ],
  },
  stopwatch: {
    candidates: [
      { token: 'create timer' },
      { token: 'query timer' },
      { token: 'remove timer' },
    ],
  },
  test: {
    candidates: [
      { token: 'run test_name' },
      { token: 'runall' },
      { token: 'clearall' },
    ],
  },
  compute: { candidates: [{ token: 'math' }] },

  help: { candidates: [] },
  op: { candidates: TARGETS },
  deop: { candidates: TARGETS },
  kick: { candidates: TARGETS },
  ban: { candidates: TARGETS },
  'ban-ip': { candidates: [{ token: '192.168.1.10' }] },
  banlist: {
    candidates: [
      { token: 'players' },
      { token: 'ips' },
    ],
  },
  pardon: { candidates: TARGETS },
  'pardon-ip': { candidates: [{ token: '192.168.1.10' }] },
  whitelist: {
    candidates: [
      { token: 'add <player>' },
      { token: 'remove <player>' },
      { token: 'list' },
      { token: 'on' },
      { token: 'off' },
    ],
  },
  'save-all': { candidates: [] },
  'save-off': { candidates: [] },
  'save-on': { candidates: [] },
  stop: { candidates: [] },
  setidletimeout: { candidates: [{ token: '5' }] },
  publish: { candidates: [] },
  transfer: { candidates: [{ token: 'localhost 25565' }] },
  version: { candidates: [] },

  perf: {
    candidates: [
      { token: 'start' },
      { token: 'stop' },
    ],
  },
  jfr: {
    candidates: [
      { token: 'start' },
      { token: 'stop' },
      { token: 'dump' },
    ],
  },
  debug: {
    candidates: [
      { token: 'start' },
      { token: 'stop' },
    ],
  },
  fetchprofile: { candidates: [{ token: 'Notch' }] },

  experience: {
    candidates: [
      { token: 'add' },
      { token: 'set' },
      { token: 'query' },
    ],
  },
};

// ======================================================================
// NBT / 物品组件：给「物品 / 实体 / 方块」补上后面还能接什么
// give 与 item 用 1.20.5+ 的方括号组件；summon 用实体 NBT；setblock/fill 用方块 NBT
// ======================================================================

/** 物品组件（跟在数量后面，如 1[custom_name=...]） */
const ITEM_COMPONENTS: Candidate[] = [
  {
    token: `1[custom_name='{"text":"Custom name"}']`,
  },
  {
    token: `1[lore=['{"text":"First line"}','{"text":"Second line"}']]`,
  },
  {
    token: `1[enchantments={levels:{"minecraft:sharpness":5}}]`,
  },
  {
    token: `1[enchantments={levels:{"minecraft:protection":4,"minecraft:unbreaking":3}}]`,
  },
  { token: '1[unbreakable={}]' },
  { token: '1[rarity="epic"]' },
  { token: '1[dyed_color={rgb:16711680}]' },
  { token: '1[damage=10]' },
  { token: '1[max_damage=1000]' },
  { token: '1[attribute_modifiers=[]]' },
  { token: '64' },
];

/** 实体 NBT（summon 的最后一个参数） */
const ENTITY_NBT: Candidate[] = [
  { token: '~ ~ ~ {NoAI:1b}' },
  { token: '~ ~ ~ {NoAI:1b,Silent:1b}' },
  { token: '~ ~ ~ {PersistenceRequired:1b}' },
  { token: '~ ~ ~ {Invulnerable:1b}' },
  { token: '~ ~ ~ {NoGravity:1b}' },
  { token: '~ ~ ~ {Glowing:1b}' },
  { token: `~ ~ ~ {CustomName:'{"text":"Guard"}',CustomNameVisible:1b}` },
  { token: '~ ~ ~ {Health:5.0f}' },
  {
    token: '~ ~ ~ {ArmorItems:[{},{},{},{id:"minecraft:diamond_helmet",count:1}]}',
  },
  {
    token: '~ ~ ~ {HandItems:[{id:"minecraft:diamond_sword",count:1},{}]}',
  },
  { token: '~ ~ ~' },
];

/** 方块 NBT（setblock / fill 的最后一个参数） */
const BLOCK_NBT: Candidate[] = [
  {
    token: '{Items:[{Slot:0b,id:"minecraft:diamond",count:64}]}',
  },
  {
    token: '{Items:[{Slot:0b,id:"minecraft:golden_apple",count:16}]}',
  },
  { token: '{Lock:"key"}' },
  { token: `{CustomName:'{"text":"Treasure Chest"}'}` },
];

/** 给每件物品生成组件候选（give 的三个目标都覆盖） */
for (const target of ['give @s', 'give @a', 'give @p']) {
  for (const item of ITEMS) {
    const key = `${target} ${item.token}`;
    if (!COMMAND_TREE[key]) {
      COMMAND_TREE[key] = { candidates: ITEM_COMPONENTS };
    }
  }
}

/** 给每种可生成实体生成 NBT 候选 */
for (const entity of ENTITIES) {
  const key = `summon ${entity.token}`;
  if (!COMMAND_TREE[key]) {
    COMMAND_TREE[key] = { candidates: ENTITY_NBT };
  }
}

/** setblock / fill 里放方块之后可以接方块 NBT */
for (const block of ITEMS.slice(0, 20)) {
  for (const base of ['setblock 0 64 0', 'fill 0 64 0 10 70 10']) {
    const key = `${base} ${block.token}`;
    if (!COMMAND_TREE[key]) {
      COMMAND_TREE[key] = { candidates: BLOCK_NBT };
    }
  }
}

/** 去掉开头的 /、压缩空白，作为查表的 key */
export function normalizeCommand(raw: string): string {
  return raw.replace(/^\//, '').replace(/\s+/g, ' ').trim();
}

/** 查当前前缀后面能接什么；返回 null 表示这里没有更多候选 */
export function lookupCandidates(raw: string): Candidate[] | null {
  const key = normalizeCommand(raw);
  if (!key) return ROOT_CANDIDATES;
  const node = COMMAND_TREE[key];
  if (!node) return null;
  return node.candidates;
}

/** 全量候选索引（带上级路径），用于关键词检索 */
export const ALL_CANDIDATES: IndexedCandidate[] = [
  ...ROOT_CANDIDATES.map((c) => ({ ...c, parent: '' })),
  ...Object.entries(COMMAND_TREE).flatMap(([parent, node]) =>
    node.candidates.map((c) => ({ ...c, parent })),
  ),
];

/** 关键词检索：匹配 token 或英文标签 */
export function searchCandidates(keyword: string, limit = 60): IndexedCandidate[] {
  const key = keyword.trim().toLowerCase();
  if (!key) return [];
  const hits = ALL_CANDIDATES.filter(
    (c) => c.token.toLowerCase().includes(key) || displayHint(c).toLowerCase().includes(key),
  );
  // Dedupe (the same token may appear under several parents)
  const seen = new Set<string>();
  const unique: IndexedCandidate[] = [];
  for (const hit of hits) {
    const id = `${hit.parent}|${hit.token}|${displayHint(hit)}`;
    if (seen.has(id)) continue;
    seen.add(id);
    unique.push(hit);
    if (unique.length >= limit) break;
  }
  return unique;
}

/** 给 Ctrl+Alt+Q 速查小窗用的扁平候选表（Python 侧检索用） */
export function buildPaletteEntries(): { token: string; hint: string; parent: string }[] {
  return ALL_CANDIDATES.map((c) => ({
    token: c.token,
    hint: displayHint(c),
    parent: c.parent,
  }));
}

/** 所有合法的指令前缀（含"没有后续候选"的完整指令），速查窗用来区分"完整"与"无效" */
export const COMMAND_NODES: string[] = Object.keys(COMMAND_TREE);
