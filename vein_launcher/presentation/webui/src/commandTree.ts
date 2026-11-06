/* 指令候选树 + 中文检索
 *
 * key     —— 归一化后的指令前缀（不含开头的 /，多个空格压成一个）
 * 候选    —— 点击后追加到输入框的 token + 中文说明
 *
 * 语法对应 Java 版 1.13+；需要世界开启作弊或拥有 OP 权限。
 */

export interface Candidate {
  /** 点击后追加的文本（数字/坐标类会填一个可直接用的默认值） */
  token: string;
  /** 中文说明 */
  hint: string;
  /** 可选分组标题，只在初始列表里用来分节 */
  group?: string;
}

export interface CommandNode {
  candidates: Candidate[];
}

/** 带上级路径的候选，用于跨层级的中文检索 */
export interface IndexedCandidate extends Candidate {
  parent: string;
}

const TARGETS: Candidate[] = [
  { token: '@s', hint: '自己' },
  { token: '@a', hint: '所有玩家' },
  { token: '@p', hint: '最近的玩家' },
  { token: '@r', hint: '随机玩家' },
  { token: '<玩家名>', hint: '指定玩家（把尖括号换成名字）' },
];

const SELECTORS: Candidate[] = [
  { token: '@e', hint: '所有实体（含生物与掉落物）' },
  { token: '@a', hint: '所有玩家' },
  { token: '@p', hint: '最近的玩家' },
  { token: '@r', hint: '随机玩家' },
  { token: '@s', hint: '自己' },
  { token: '<玩家名>', hint: '指定玩家（把尖括号换成名字）' },
];

const BOOL: Candidate[] = [
  { token: 'true', hint: '开启' },
  { token: 'false', hint: '关闭' },
];

/** 物品表：按"常用度 + 分类"排，hint 全部中文，可被中文检索 */
const ITEMS: Candidate[] = [
  // ---------------- 方块
  { token: 'minecraft:stone', hint: '石头' },
  { token: 'minecraft:cobblestone', hint: '圆石' },
  { token: 'minecraft:dirt', hint: '泥土' },
  { token: 'minecraft:grass_block', hint: '草方块' },
  { token: 'minecraft:sand', hint: '沙子' },
  { token: 'minecraft:gravel', hint: '沙砾' },
  { token: 'minecraft:oak_log', hint: '橡木原木' },
  { token: 'minecraft:oak_planks', hint: '橡木木板' },
  { token: 'minecraft:glass', hint: '玻璃' },
  { token: 'minecraft:bricks', hint: '砖块' },
  { token: 'minecraft:obsidian', hint: '黑曜石' },
  { token: 'minecraft:netherrack', hint: '下界岩' },
  { token: 'minecraft:end_stone', hint: '末地石' },
  { token: 'minecraft:sandstone', hint: '砂岩' },
  { token: 'minecraft:deepslate', hint: '深板岩' },
  { token: 'minecraft:iron_block', hint: '铁块' },
  { token: 'minecraft:gold_block', hint: '金块' },
  { token: 'minecraft:diamond_block', hint: '钻石块' },
  { token: 'minecraft:emerald_block', hint: '绿宝石块' },
  { token: 'minecraft:netherite_block', hint: '下界合金块' },
  { token: 'minecraft:coal_block', hint: '煤炭块' },
  { token: 'minecraft:redstone_block', hint: '红石块' },
  { token: 'minecraft:quartz_block', hint: '石英块' },
  { token: 'minecraft:glowstone', hint: '荧石' },
  { token: 'minecraft:sea_lantern', hint: '海晶灯' },
  { token: 'minecraft:torch', hint: '火把' },
  { token: 'minecraft:ladder', hint: '梯子' },
  { token: 'minecraft:chest', hint: '箱子' },
  { token: 'minecraft:furnace', hint: '熔炉' },
  { token: 'minecraft:crafting_table', hint: '工作台' },
  { token: 'minecraft:anvil', hint: '铁砧' },
  { token: 'minecraft:enchanting_table', hint: '附魔台' },
  { token: 'minecraft:beacon', hint: '信标' },
  { token: 'minecraft:hopper', hint: '漏斗' },
  { token: 'minecraft:ender_chest', hint: '末影箱' },
  { token: 'minecraft:shulker_box', hint: '潜影盒' },
  { token: 'minecraft:tnt', hint: 'TNT' },
  { token: 'minecraft:scaffolding', hint: '脚手架' },
  { token: 'minecraft:lightning_rod', hint: '避雷针' },
  { token: 'minecraft:target', hint: '标靶' },
  { token: 'minecraft:note_block', hint: '音符盒' },
  { token: 'minecraft:jukebox', hint: '唱片机' },
  { token: 'minecraft:conduit', hint: '潮涌核心' },
  { token: 'minecraft:amethyst_block', hint: '紫水晶块' },
  { token: 'minecraft:copper_block', hint: '铜块' },

  // ---------------- 工具 / 武器 / 盔甲
  { token: 'minecraft:iron_sword', hint: '铁剑' },
  { token: 'minecraft:diamond_sword', hint: '钻石剑' },
  { token: 'minecraft:netherite_sword', hint: '下界合金剑' },
  { token: 'minecraft:stone_sword', hint: '石剑' },
  { token: 'minecraft:wooden_sword', hint: '木剑' },
  { token: 'minecraft:bow', hint: '弓' },
  { token: 'minecraft:crossbow', hint: '弩' },
  { token: 'minecraft:arrow', hint: '箭' },
  { token: 'minecraft:spectral_arrow', hint: '光灵箭' },
  { token: 'minecraft:trident', hint: '三叉戟' },
  { token: 'minecraft:shield', hint: '盾牌' },
  { token: 'minecraft:iron_pickaxe', hint: '铁镐' },
  { token: 'minecraft:diamond_pickaxe', hint: '钻石镐' },
  { token: 'minecraft:netherite_pickaxe', hint: '下界合金镐' },
  { token: 'minecraft:iron_axe', hint: '铁斧' },
  { token: 'minecraft:diamond_axe', hint: '钻石斧' },
  { token: 'minecraft:iron_shovel', hint: '铁锹' },
  { token: 'minecraft:fishing_rod', hint: '钓鱼竿' },
  { token: 'minecraft:flint_and_steel', hint: '打火石' },
  { token: 'minecraft:shears', hint: '剪刀' },
  { token: 'minecraft:elytra', hint: '鞘翅' },
  { token: 'minecraft:iron_helmet', hint: '铁头盔' },
  { token: 'minecraft:iron_chestplate', hint: '铁胸甲' },
  { token: 'minecraft:iron_leggings', hint: '铁护腿' },
  { token: 'minecraft:iron_boots', hint: '铁靴子' },
  { token: 'minecraft:diamond_helmet', hint: '钻石头盔' },
  { token: 'minecraft:diamond_chestplate', hint: '钻石胸甲' },
  { token: 'minecraft:diamond_leggings', hint: '钻石护腿' },
  { token: 'minecraft:diamond_boots', hint: '钻石靴子' },
  { token: 'minecraft:netherite_chestplate', hint: '下界合金胸甲' },
  { token: 'minecraft:turtle_helmet', hint: '海龟壳' },
  { token: 'minecraft:carrot_on_a_stick', hint: '胡萝卜钓竿' },

  // ---------------- 食物
  { token: 'minecraft:apple', hint: '苹果' },
  { token: 'minecraft:golden_apple', hint: '金苹果' },
  { token: 'minecraft:enchanted_golden_apple', hint: '附魔金苹果' },
  { token: 'minecraft:bread', hint: '面包' },
  { token: 'minecraft:cooked_beef', hint: '牛排' },
  { token: 'minecraft:cooked_porkchop', hint: '熟猪排' },
  { token: 'minecraft:cooked_chicken', hint: '熟鸡肉' },
  { token: 'minecraft:golden_carrot', hint: '金胡萝卜' },
  { token: 'minecraft:carrot', hint: '胡萝卜' },
  { token: 'minecraft:potato', hint: '马铃薯' },
  { token: 'minecraft:baked_potato', hint: '烤马铃薯' },
  { token: 'minecraft:melon_slice', hint: '西瓜片' },
  { token: 'minecraft:cookie', hint: '曲奇' },
  { token: 'minecraft:cake', hint: '蛋糕' },
  { token: 'minecraft:pumpkin_pie', hint: '南瓜派' },
  { token: 'minecraft:sweet_berries', hint: '甜浆果' },
  { token: 'minecraft:honey_bottle', hint: '蜂蜜瓶' },

  // ---------------- 材料
  { token: 'minecraft:stick', hint: '木棍' },
  { token: 'minecraft:coal', hint: '煤炭' },
  { token: 'minecraft:charcoal', hint: '木炭' },
  { token: 'minecraft:iron_ingot', hint: '铁锭' },
  { token: 'minecraft:gold_ingot', hint: '金锭' },
  { token: 'minecraft:copper_ingot', hint: '铜锭' },
  { token: 'minecraft:diamond', hint: '钻石' },
  { token: 'minecraft:emerald', hint: '绿宝石' },
  { token: 'minecraft:netherite_ingot', hint: '下界合金锭' },
  { token: 'minecraft:netherite_scrap', hint: '下界合金碎片' },
  { token: 'minecraft:lapis_lazuli', hint: '青金石' },
  { token: 'minecraft:redstone', hint: '红石' },
  { token: 'minecraft:quartz', hint: '下界石英' },
  { token: 'minecraft:amethyst_shard', hint: '紫水晶碎片' },
  { token: 'minecraft:string', hint: '线' },
  { token: 'minecraft:leather', hint: '皮革' },
  { token: 'minecraft:feather', hint: '羽毛' },
  { token: 'minecraft:flint', hint: '燧石' },
  { token: 'minecraft:gunpowder', hint: '火药' },
  { token: 'minecraft:blaze_rod', hint: '烈焰棒' },
  { token: 'minecraft:blaze_powder', hint: '烈焰粉' },
  { token: 'minecraft:ender_pearl', hint: '末影珍珠' },
  { token: 'minecraft:ender_eye', hint: '末影之眼' },
  { token: 'minecraft:slime_ball', hint: '黏液球' },
  { token: 'minecraft:ghast_tear', hint: '恶魂之泪' },
  { token: 'minecraft:nether_star', hint: '下界之星' },
  { token: 'minecraft:totem_of_undying', hint: '不死图腾' },
  { token: 'minecraft:ink_sac', hint: '墨囊' },
  { token: 'minecraft:glow_ink_sac', hint: '荧光墨囊' },
  { token: 'minecraft:bone', hint: '骨头' },
  { token: 'minecraft:bone_meal', hint: '骨粉' },
  { token: 'minecraft:sugar', hint: '糖' },
  { token: 'minecraft:paper', hint: '纸' },
  { token: 'minecraft:book', hint: '书' },
  { token: 'minecraft:enchanted_book', hint: '附魔书' },
  { token: 'minecraft:writable_book', hint: '书与笔' },
  { token: 'minecraft:name_tag', hint: '命名牌' },
  { token: 'minecraft:saddle', hint: '鞍' },
  { token: 'minecraft:dragon_breath', hint: '龙息' },
  { token: 'minecraft:experience_bottle', hint: '附魔之瓶' },
  { token: 'minecraft:glass_bottle', hint: '玻璃瓶' },

  // ---------------- 红石 / 载具 / 杂项
  { token: 'minecraft:redstone_torch', hint: '红石火把' },
  { token: 'minecraft:repeater', hint: '红石中继器' },
  { token: 'minecraft:comparator', hint: '红石比较器' },
  { token: 'minecraft:piston', hint: '活塞' },
  { token: 'minecraft:sticky_piston', hint: '黏性活塞' },
  { token: 'minecraft:observer', hint: '侦测器' },
  { token: 'minecraft:dispenser', hint: '发射器' },
  { token: 'minecraft:dropper', hint: '投掷器' },
  { token: 'minecraft:rail', hint: '铁轨' },
  { token: 'minecraft:powered_rail', hint: '动力铁轨' },
  { token: 'minecraft:minecart', hint: '矿车' },
  { token: 'minecraft:bucket', hint: '桶' },
  { token: 'minecraft:water_bucket', hint: '水桶' },
  { token: 'minecraft:lava_bucket', hint: '熔岩桶' },
  { token: 'minecraft:milk_bucket', hint: '牛奶桶' },
  { token: 'minecraft:item_frame', hint: '物品展示框' },
  { token: 'minecraft:armor_stand', hint: '盔甲架' },
  { token: 'minecraft:painting', hint: '画' },
  { token: 'minecraft:compass', hint: '指南针' },
  { token: 'minecraft:clock', hint: '钟' },
  { token: 'minecraft:map', hint: '地图' },
  { token: 'minecraft:spyglass', hint: '望远镜' },
  { token: 'minecraft:recovery_compass', hint: '追溯指针' },
  { token: 'minecraft:lodestone', hint: '磁石' },
  { token: 'minecraft:end_crystal', hint: '末地水晶' },
  { token: 'minecraft:firework_rocket', hint: '烟花火箭' },
];

const EFFECTS: Candidate[] = [
  { token: 'minecraft:regeneration', hint: '生命恢复' },
  { token: 'minecraft:speed', hint: '速度' },
  { token: 'minecraft:strength', hint: '力量' },
  { token: 'minecraft:night_vision', hint: '夜视' },
  { token: 'minecraft:fire_resistance', hint: '抗火' },
  { token: 'minecraft:water_breathing', hint: '水下呼吸' },
  { token: 'minecraft:absorption', hint: '伤害吸收' },
  { token: 'minecraft:invisibility', hint: '隐身' },
  { token: 'minecraft:jump_boost', hint: '跳跃提升' },
  { token: 'minecraft:haste', hint: '急迫（挖掘加速）' },
  { token: 'minecraft:luck', hint: '幸运' },
];

const ENTITIES: Candidate[] = [
  { token: 'minecraft:zombie', hint: '僵尸' },
  { token: 'minecraft:skeleton', hint: '骷髅' },
  { token: 'minecraft:creeper', hint: '苦力怕' },
  { token: 'minecraft:spider', hint: '蜘蛛' },
  { token: 'minecraft:enderman', hint: '末影人' },
  { token: 'minecraft:villager', hint: '村民' },
  { token: 'minecraft:cow', hint: '牛' },
  { token: 'minecraft:pig', hint: '猪' },
  { token: 'minecraft:sheep', hint: '羊' },
  { token: 'minecraft:chicken', hint: '鸡' },
  { token: 'minecraft:horse', hint: '马' },
  { token: 'minecraft:wolf', hint: '狼' },
  { token: 'minecraft:iron_golem', hint: '铁傀儡' },
];

const GAMEMODES: Candidate[] = [
  { token: 'survival', hint: '生存' },
  { token: 'creative', hint: '创造' },
  { token: 'adventure', hint: '冒险' },
  { token: 'spectator', hint: '旁观' },
];

const TIME_VALUES: Candidate[] = [
  { token: 'day', hint: '白天（1000 tick）' },
  { token: 'noon', hint: '正午（6000 tick）' },
  { token: 'night', hint: '夜晚（13000 tick）' },
  { token: 'midnight', hint: '午夜（18000 tick）' },
  { token: '1000', hint: '直接填 tick 数字（示例 1000）' },
];

const GAMERULES: Candidate[] = [
  { token: 'keepInventory', hint: '死亡是否保留物品' },
  { token: 'doDaylightCycle', hint: '昼夜是否循环' },
  { token: 'doMobSpawning', hint: '是否自然生成生物' },
  { token: 'doFireTick', hint: '火是否蔓延' },
  { token: 'mobGriefing', hint: '生物是否破坏方块' },
  { token: 'showCoordinates', hint: '是否显示坐标' },
];

/** 指令总表：覆盖 Java 版 1.21 的全部指令（来源：minecraft.wiki/w/Commands） */
export const ROOT_CANDIDATES: Candidate[] = [
  // ---------------- 基础
  { token: 'gamemode', hint: '切换游戏模式', group: '基础' },
  { token: 'defaultgamemode', hint: '设置新玩家的默认游戏模式', group: '基础' },
  { token: 'difficulty', hint: '设置游戏难度', group: '基础' },
  { token: 'tp', hint: '传送实体（teleport 的简写）', group: '基础' },
  { token: 'teleport', hint: '传送实体', group: '基础' },
  { token: 'kill', hint: '清除实体', group: '基础' },
  { token: 'clear', hint: '清空物品栏', group: '基础' },
  { token: 'effect', hint: '管理状态效果', group: '基础' },
  { token: 'enchant', hint: '给手持物品附魔', group: '基础' },
  { token: 'xp', hint: '给予经验', group: '基础' },
  { token: 'experience', hint: '给予经验（xp 的全称）', group: '基础' },
  { token: 'give', hint: '给予物品', group: '基础' },
  { token: 'item', hint: '修改物品栏里的物品', group: '基础' },
  { token: 'recipe', hint: '解锁 / 锁定配方', group: '基础' },
  { token: 'advancement', hint: '授予 / 撤销进度', group: '基础' },
  { token: 'spawnpoint', hint: '设置个人重生点', group: '基础' },
  { token: 'setworldspawn', hint: '设置世界出生点', group: '基础' },

  // ---------------- 世界与方块
  { token: 'time', hint: '查询/修改世界时间', group: '世界与方块' },
  { token: 'weather', hint: '设置天气', group: '世界与方块' },
  { token: 'gamerule', hint: '修改世界规则', group: '世界与方块' },
  { token: 'setblock', hint: '在指定位置放置方块', group: '世界与方块' },
  { token: 'fill', hint: '批量填充方块', group: '世界与方块' },
  { token: 'clone', hint: '复制一块区域的方块', group: '世界与方块' },
  { token: 'fillbiome', hint: '批量设置群系', group: '世界与方块' },
  { token: 'place', hint: '放置结构 / 地物 / 拼图', group: '世界与方块' },
  { token: 'locate', hint: '定位结构或群系', group: '世界与方块' },
  { token: 'forceload', hint: '强制加载/卸载区块', group: '世界与方块' },
  { token: 'worldborder', hint: '世界边界大小与伤害', group: '世界与方块' },
  { token: 'seed', hint: '查看世界种子', group: '世界与方块' },

  // ---------------- 实体与状态
  { token: 'summon', hint: '生成实体', group: '实体与状态' },
  { token: 'attribute', hint: '查询/修改实体属性', group: '实体与状态' },
  { token: 'damage', hint: '对实体造成伤害', group: '实体与状态' },
  { token: 'ride', hint: '让实体骑乘/下车', group: '实体与状态' },
  { token: 'rotate', hint: '旋转实体朝向', group: '实体与状态' },
  { token: 'spectate', hint: '旁观指定玩家', group: '实体与状态' },
  { token: 'tag', hint: '给实体打标签', group: '实体与状态' },
  { token: 'team', hint: '队伍管理', group: '实体与状态' },
  { token: 'teammsg', hint: '给队伍发消息', group: '实体与状态' },
  { token: 'spreadplayers', hint: '把玩家分散到区域内', group: '实体与状态' },
  { token: 'loot', hint: '掉落战利品表物品', group: '实体与状态' },
  { token: 'particle', hint: '生成粒子效果', group: '实体与状态' },
  { token: 'playsound', hint: '播放音效', group: '实体与状态' },
  { token: 'stopsound', hint: '停止音效', group: '实体与状态' },
  { token: 'posteffect', hint: '屏幕后处理特效', group: '实体与状态' },

  // ---------------- 消息与显示
  { token: 'say', hint: '向全服发送公告', group: '消息与显示' },
  { token: 'me', hint: '显示一条"我做了某事"的消息', group: '消息与显示' },
  { token: 'tell', hint: '给玩家发私聊', group: '消息与显示' },
  { token: 'msg', hint: '私聊（tell 的别名）', group: '消息与显示' },
  { token: 'tellraw', hint: '发送原始 JSON 消息', group: '消息与显示' },
  { token: 'title', hint: '屏幕标题 / 副标题 / 动作栏', group: '消息与显示' },
  { token: 'bossbar', hint: '创建与管理 BOSS 栏', group: '消息与显示' },
  { token: 'dialog', hint: '向玩家弹出对话框', group: '消息与显示' },

  // ---------------- 逻辑与数据
  { token: 'execute', hint: '带条件地执行其它指令', group: '逻辑与数据' },
  { token: 'function', hint: '运行数据包里的函数', group: '逻辑与数据' },
  { token: 'schedule', hint: '定时执行函数', group: '逻辑与数据' },
  { token: 'datapack', hint: '数据包列表 / 启用 / 禁用', group: '逻辑与数据' },
  { token: 'reload', hint: '重载数据包', group: '逻辑与数据' },
  { token: 'data', hint: '读写方块/实体的 NBT', group: '逻辑与数据' },
  { token: 'scoreboard', hint: '计分板与队伍分数', group: '逻辑与数据' },
  { token: 'random', hint: '随机数', group: '逻辑与数据' },
  { token: 'return', hint: '函数返回值', group: '逻辑与数据' },
  { token: 'tick', hint: '控制刻循环（暂停/步进）', group: '逻辑与数据' },
  { token: 'stopwatch', hint: '计时器', group: '逻辑与数据' },
  { token: 'test', hint: '运行游戏测试', group: '逻辑与数据' },
  { token: 'compute', hint: '计算数字提供器', group: '逻辑与数据' },

  // ---------------- 服务器管理
  { token: 'list', hint: '列出在线玩家', group: '服务器管理' },
  { token: 'help', hint: '查看指令帮助', group: '服务器管理' },
  { token: 'op', hint: '授予管理员', group: '服务器管理' },
  { token: 'deop', hint: '取消管理员', group: '服务器管理' },
  { token: 'kick', hint: '踢出玩家', group: '服务器管理' },
  { token: 'ban', hint: '封禁玩家', group: '服务器管理' },
  { token: 'ban-ip', hint: '封禁 IP', group: '服务器管理' },
  { token: 'banlist', hint: '查看封禁列表', group: '服务器管理' },
  { token: 'pardon', hint: '解除玩家封禁', group: '服务器管理' },
  { token: 'pardon-ip', hint: '解除 IP 封禁', group: '服务器管理' },
  { token: 'whitelist', hint: '白名单管理', group: '服务器管理' },
  { token: 'save-all', hint: '立即保存存档', group: '服务器管理' },
  { token: 'save-off', hint: '关闭自动保存', group: '服务器管理' },
  { token: 'save-on', hint: '开启自动保存', group: '服务器管理' },
  { token: 'stop', hint: '关闭服务器', group: '服务器管理' },
  { token: 'setidletimeout', hint: '挂机踢出时间（分钟）', group: '服务器管理' },
  { token: 'publish', hint: '把单人存档开放到局域网', group: '服务器管理' },
  { token: 'transfer', hint: '把玩家转移到其它服务器', group: '服务器管理' },
  { token: 'version', hint: '查看游戏版本', group: '服务器管理' },

  // ---------------- 调试
  { token: 'perf', hint: '性能分析 10 秒', group: '调试' },
  { token: 'jfr', hint: 'JFR 性能记录', group: '调试' },
  { token: 'debug', hint: '开始 / 结束调试会话', group: '调试' },
  { token: 'fetchprofile', hint: '获取玩家档案', group: '调试' },
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
      { token: '[type=!player]', hint: '排除玩家，只清生物/掉落物' },
      { token: '[type=minecraft:zombie]', hint: '只清僵尸' },
      { token: '[distance=..10]', hint: '10 格以内' },
      { token: '[limit=1]', hint: '最多处理 1 个' },
      { token: '[sort=nearest]', hint: '按最近优先排序' },
    ],
  },
  'kill @a': {
    candidates: [
      { token: '[limit=1]', hint: '只处理 1 名玩家' },
      { token: '[distance=..5]', hint: '5 格以内' },
    ],
  },
  'kill @p': { candidates: [] },
  'kill @r': { candidates: [] },
  'kill @s': { candidates: [] },

  // ---------------------------------------------------------------- tp
  tp: { candidates: TARGETS },
  'tp @s': {
    candidates: [
      { token: '0 100 0', hint: '传送到坐标 (0,100,0)' },
      { token: '~ ~ ~', hint: '原地不动（常配合后面的修饰）' },
      { token: '~ ~1 ~', hint: '向上 1 格' },
      { token: '@p', hint: '传送到最近的玩家' },
    ],
  },
  'tp @a': { candidates: [{ token: '0 100 0', hint: '全部传送过去' }] },

  // ---------------------------------------------------------------- give
  give: { candidates: TARGETS },
  'give @s': { candidates: ITEMS },
  'give @a': { candidates: ITEMS },
  'give @p': { candidates: ITEMS },

  // ---------------------------------------------------------------- effect
  effect: {
    candidates: [
      { token: 'give', hint: '施加状态效果' },
      { token: 'clear', hint: '清除状态效果' },
    ],
  },
  'effect give': { candidates: TARGETS },
  'effect clear': { candidates: TARGETS },
  'effect give @s': { candidates: EFFECTS },
  'effect give @a': { candidates: EFFECTS },

  // ---------------------------------------------------------------- time
  time: {
    candidates: [
      { token: 'set', hint: '设置到某个时间' },
      { token: 'add', hint: '在当前时间上加/减' },
      { token: 'query', hint: '查询当前时间' },
    ],
  },
  'time set': { candidates: TIME_VALUES },
  'time add': {
    candidates: [
      { token: '1000', hint: '增加 1000 tick（约半天）' },
      { token: '-1000', hint: '减少 1000 tick' },
    ],
  },
  'time query': {
    candidates: [
      { token: 'daytime', hint: '当天的 tick（0-23999）' },
      { token: 'day', hint: '游戏内天数' },
    ],
  },

  // ---------------------------------------------------------------- weather
  weather: {
    candidates: [
      { token: 'clear', hint: '晴天' },
      { token: 'rain', hint: '下雨（含雪地）' },
      { token: 'thunder', hint: '雷雨' },
    ],
  },
  'weather clear': { candidates: [{ token: '6000', hint: '持续秒数（示例 6000）' }] },
  'weather rain': { candidates: [{ token: '6000', hint: '持续秒数（示例 6000）' }] },
  'weather thunder': { candidates: [{ token: '6000', hint: '持续秒数（示例 6000）' }] },

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
      { token: '~ ~ ~', hint: '用当前位置（默认）' },
      { token: '0 64 0', hint: '指定坐标' },
    ],
  },
  summon: { candidates: ENTITIES },
  enchant: { candidates: TARGETS },
  'enchant @s': {
    candidates: [
      { token: 'minecraft:sharpness', hint: '锋利（剑/斧）' },
      { token: 'minecraft:protection', hint: '保护（盔甲）' },
      { token: 'minecraft:unbreaking', hint: '耐久（多数物品）' },
      { token: 'minecraft:efficiency', hint: '效率（镐/斧/铲）' },
      { token: 'minecraft:fortune', hint: '时运（镐/斧/铲）' },
      { token: 'minecraft:power', hint: '力量（弓）' },
    ],
  },

  // ---------------------------------------------------------------- xp / 方块操作
  xp: {
    candidates: [
      { token: 'add', hint: '增加经验' },
      { token: 'set', hint: '设置经验' },
      { token: 'query', hint: '查询经验' },
    ],
  },
  'xp add': { candidates: TARGETS },
  'xp add @s': {
    candidates: [
      { token: '30 levels', hint: '加 30 级' },
      { token: '100 points', hint: '加 100 点经验' },
    ],
  },
  setblock: { candidates: [{ token: '0 64 0', hint: '目标坐标（示例）' }] },
  'setblock 0 64 0': { candidates: ITEMS.slice(0, 20) },
  fill: { candidates: [{ token: '0 64 0 10 70 10', hint: '起止坐标（示例）' }] },
  'fill 0 64 0 10 70 10': { candidates: ITEMS.slice(0, 20) },
  locate: {
    candidates: [
      { token: 'structure village', hint: '最近的村庄' },
      { token: 'structure fortress', hint: '最近的下界要塞' },
      { token: 'structure stronghold', hint: '最近的末地要塞' },
      { token: 'biome plains', hint: '最近的平原群系' },
    ],
  },
  playsound: {
    candidates: [
      { token: 'minecraft:entity.player.levelup', hint: '升级音效' },
      { token: 'minecraft:entity.experience_orb.pickup', hint: '拾取经验音' },
      { token: 'minecraft:block.note_block.harp', hint: '音符盒（竖琴）' },
    ],
  },
  difficulty: {
    candidates: [
      { token: 'peaceful', hint: '和平' },
      { token: 'easy', hint: '简单' },
      { token: 'normal', hint: '普通' },
      { token: 'hard', hint: '困难' },
    ],
  },
  seed: { candidates: [] },
  list: { candidates: [] },

  // ================================================================ 1.21 全量指令分支
  defaultgamemode: { candidates: GAMEMODES },
  teleport: { candidates: TARGETS },
  'teleport @s': {
    candidates: [
      { token: '0 100 0', hint: '传送到坐标 (0,100,0)' },
      { token: '~ ~1 ~', hint: '向上 1 格' },
      { token: '@p', hint: '传送到最近的玩家' },
    ],
  },

  advancement: {
    candidates: [
      { token: 'grant', hint: '授予进度' },
      { token: 'revoke', hint: '撤销进度' },
    ],
  },
  'advancement grant': { candidates: TARGETS },
  'advancement grant @s': {
    candidates: [
      { token: 'everything', hint: '所有进度' },
      { token: 'only minecraft:story/root', hint: '只给指定进度（示例）' },
      { token: 'from minecraft:story/root', hint: '给该进度及其下游' },
    ],
  },
  'advancement revoke': { candidates: TARGETS },
  'advancement revoke @s': { candidates: [{ token: 'everything', hint: '撤销所有进度' }] },

  item: {
    candidates: [
      { token: 'replace', hint: '替换物品栏格子里的物品' },
      { token: 'modify', hint: '修改物品属性' },
    ],
  },
  'item replace': { candidates: TARGETS },
  'item replace entity @s': {
    candidates: [
      { token: 'weapon.mainhand', hint: '主手' },
      { token: 'weapon.offhand', hint: '副手' },
      { token: 'armor.head', hint: '头盔' },
      { token: 'inventory.0', hint: '快捷栏第 1 格' },
    ],
  },
  'item replace entity @s weapon.mainhand': {
    candidates: [
      { token: 'with minecraft:diamond_sword', hint: '换成钻石剑' },
      { token: 'with minecraft:golden_apple 16', hint: '换成 16 个金苹果' },
    ],
  },

  recipe: {
    candidates: [
      { token: 'give', hint: '解锁配方' },
      { token: 'take', hint: '锁定配方' },
    ],
  },
  'recipe give': { candidates: TARGETS },
  'recipe give @s': { candidates: [{ token: '*', hint: '全部配方' }] },

  clone: { candidates: [{ token: '0 64 0 5 70 5 10 64 0', hint: '把 (0..5) 区域复制到 (10,64,0)' }] },
  'clone 0 64 0 5 70 5 10 64 0': {
    candidates: [
      { token: 'replace', hint: '覆盖目标区域' },
      { token: 'masked', hint: '只复制非空气方块' },
      { token: 'force', hint: '允许与源区域重叠' },
    ],
  },

  fillbiome: { candidates: [{ token: '0 64 0 10 70 10 minecraft:plains', hint: '把区域群系设为平原' }] },

  place: {
    candidates: [
      { token: 'feature minecraft:oak', hint: '生成一棵橡树（地物）' },
      { token: 'structure minecraft:village_plains', hint: '生成结构' },
      { token: 'jigsaw minecraft:village/plains/houses/plains_small_house_1', hint: '生成拼图结构' },
      { token: 'template minecraft:village/plains/houses/plains_small_house_1', hint: '放置结构模板' },
    ],
  },

  forceload: {
    candidates: [
      { token: 'add', hint: '强制加载区块' },
      { token: 'remove', hint: '取消强制加载' },
      { token: 'query', hint: '查询已强制加载的区块' },
    ],
  },
  'forceload add': { candidates: [{ token: '0 0', hint: '区块坐标（示例）' }] },

  worldborder: {
    candidates: [
      { token: 'set', hint: '设置边界大小' },
      { token: 'center', hint: '设置边界中心' },
      { token: 'add', hint: '扩大/缩小边界' },
      { token: 'damage', hint: '设置越界伤害' },
      { token: 'get', hint: '查询当前边界' },
    ],
  },
  'worldborder set': { candidates: [{ token: '100', hint: '直径 100 格' }] },
  'worldborder center': { candidates: [{ token: '0 0', hint: '以 (0,0) 为中心' }] },
  'worldborder damage': {
    candidates: [
      { token: 'amount 1', hint: '每秒伤害 1' },
      { token: 'buffer 5', hint: '边界外 5 格开始受伤' },
    ],
  },

  setworldspawn: { candidates: [{ token: '0 64 0', hint: '世界出生点（示例坐标）' }] },

  attribute: { candidates: TARGETS },
  'attribute @s': {
    candidates: [
      { token: 'minecraft:generic.max_health get', hint: '查询最大生命' },
      { token: 'minecraft:generic.movement_speed get', hint: '查询移动速度' },
      { token: 'minecraft:generic.attack_damage base set 100', hint: '把攻击力设为 100' },
    ],
  },

  damage: { candidates: TARGETS },
  'damage @s': { candidates: [{ token: '10', hint: '造成 10 点伤害' }] },
  'damage @e[type=!player]': { candidates: [{ token: '5', hint: '对非玩家实体造成 5 点伤害' }] },

  ride: { candidates: TARGETS },
  'ride @s': {
    candidates: [
      { token: 'mount @p', hint: '骑到最近的玩家身上' },
      { token: 'dismount', hint: '下车' },
    ],
  },
  rotate: { candidates: TARGETS },
  'rotate @s': { candidates: [{ token: '90 0', hint: '朝向东（yaw 90, pitch 0）' }] },
  spectate: { candidates: TARGETS },

  tag: { candidates: TARGETS },
  'tag @s': {
    candidates: [
      { token: 'add 测试', hint: '加上标签「测试」' },
      { token: 'remove 测试', hint: '移除标签「测试」' },
      { token: 'list', hint: '列出该实体的标签' },
    ],
  },
  team: {
    candidates: [
      { token: 'add 红队', hint: '创建队伍「红队」' },
      { token: 'list', hint: '列出所有队伍' },
      { token: 'join 红队', hint: '加入队伍' },
      { token: 'leave 红队', hint: '离开队伍' },
      { token: 'remove 红队', hint: '删除队伍' },
    ],
  },
  'team join': { candidates: TARGETS },
  teammsg: { candidates: [{ token: '大家好', hint: '给队伍发消息（示例文本）' }] },

  spreadplayers: {
    candidates: [{ token: '0 0 10 10 false @a', hint: '把玩家分散到 (0,0) 周围 10 格' }],
  },

  loot: {
    candidates: [
      { token: 'give @s minecraft:chests/simple_dungeon', hint: '把地牢战利品箱内容给自己' },
      { token: 'spawn 0 64 0 minecraft:chests/simple_dungeon', hint: '在指定位置掉落' },
      { token: 'insert 0 64 0 minecraft:chests/simple_dungeon', hint: '塞进指定容器' },
    ],
  },

  particle: {
    candidates: [
      { token: 'minecraft:flame ~ ~1 ~ 0 0 0 0 20', hint: '火焰粒子（20 个）' },
      { token: 'minecraft:heart ~ ~1 ~ 0 0 0 0 10', hint: '爱心粒子' },
      { token: 'minecraft:happy_villager ~ ~1 ~ 0 0 0 0 30', hint: '村民开心粒子' },
      { token: 'minecraft:explosion ~ ~1 ~ 0 0 0 0 5', hint: '爆炸粒子' },
    ],
  },

  stopsound: { candidates: TARGETS },
  posteffect: {
    candidates: [
      { token: 'give @s minecraft:invert', hint: '反色滤镜' },
      { token: 'give @s minecraft:notch', hint: 'Notch 滤镜' },
      { token: 'clear @s', hint: '清除后处理' },
    ],
  },

  say: { candidates: [] },
  me: { candidates: [] },
  tell: { candidates: TARGETS },
  msg: { candidates: TARGETS },
  tellraw: { candidates: TARGETS },
  'tellraw @a': { candidates: [{ token: '{"text":"你好"}', hint: '原始 JSON 文本（示例）' }] },
  title: { candidates: TARGETS },
  'title @a': {
    candidates: [
      { token: 'title 欢迎', hint: '主标题' },
      { token: 'subtitle 副标题', hint: '副标题' },
      { token: 'actionbar 提示', hint: '动作栏文字' },
      { token: 'times 10 70 20', hint: '淡入/停留/淡出（tick）' },
      { token: 'clear', hint: '清除标题' },
    ],
  },
  bossbar: {
    candidates: [
      { token: 'add minecraft:custom 名字', hint: '新建 BOSS 栏（示例）' },
      { token: 'remove minecraft:custom', hint: '删除 BOSS 栏' },
      { token: 'list', hint: '列出所有 BOSS 栏' },
      { token: 'set minecraft:custom value 50', hint: '设置进度 50' },
    ],
  },
  dialog: {
    candidates: [
      { token: 'show @a minecraft:server_links', hint: '弹出指定对话框（示例）' },
      { token: 'clear @a', hint: '关闭对话框' },
    ],
  },

  execute: {
    candidates: [
      { token: 'as @a at @s run tp ~ ~1 ~', hint: '所有玩家各向上传 1 格' },
      { token: 'if entity @a run say 有人在线', hint: '条件判断：有玩家在线才执行' },
      { token: 'positioned 0 64 0 run setblock ~ ~ ~ minecraft:stone', hint: '把执行位置挪到坐标（示例）' },
    ],
  },
  function: { candidates: [{ token: 'minecraft:test', hint: '运行数据包函数（示例）' }] },
  schedule: {
    candidates: [
      { token: 'function minecraft:test 10s', hint: '10 秒后执行一次' },
      { token: 'function minecraft:test 5t', hint: '5 tick 后执行一次' },
      { token: 'clear minecraft:test', hint: '取消该函数的定时' },
    ],
  },
  datapack: {
    candidates: [
      { token: 'list', hint: '列出已加载数据包' },
      { token: 'enable 数据包名', hint: '启用数据包（示例）' },
      { token: 'disable 数据包名', hint: '禁用数据包（示例）' },
    ],
  },
  reload: { candidates: [] },
  data: {
    candidates: [
      { token: 'get entity @s', hint: '查看实体 NBT' },
      { token: 'get block 0 64 0', hint: '查看方块实体 NBT' },
      { token: 'get storage minecraft:test', hint: '查看命令存储' },
      { token: 'merge entity @s {"Tags":["测试"]}', hint: '合并写入 NBT（示例）' },
    ],
  },
  scoreboard: {
    candidates: [
      { token: 'objectives add 分数 dummy', hint: '新建计分项「分数」' },
      { token: 'objectives list', hint: '列出计分项' },
      { token: 'players set @s 分数 100', hint: '把自己的分数设为 100' },
      { token: 'players list @s', hint: '查看某玩家分数' },
    ],
  },
  random: {
    candidates: [
      { token: 'value 1..6', hint: '取 1-6 的随机数' },
      { token: 'reset *', hint: '重置随机序列' },
    ],
  },
  return: { candidates: [{ token: '1', hint: '返回成功值 1' }] },
  tick: {
    candidates: [
      { token: 'freeze', hint: '冻结游戏刻' },
      { token: 'unfreeze', hint: '解除冻结' },
      { token: 'step 1', hint: '单步推进 1 tick' },
      { token: 'rate 20', hint: '刻速率设为 20' },
      { token: 'query', hint: '查询当前刻状态' },
    ],
  },
  stopwatch: {
    candidates: [
      { token: 'create 计时', hint: '新建计时器「计时」' },
      { token: 'query 计时', hint: '查询计时' },
      { token: 'remove 计时', hint: '删除计时器' },
    ],
  },
  test: {
    candidates: [
      { token: 'run 测试名', hint: '运行指定测试' },
      { token: 'runall', hint: '运行全部测试' },
      { token: 'clearall', hint: '清空测试结构' },
    ],
  },
  compute: { candidates: [{ token: 'math', hint: '数学计算（示例）' }] },

  help: { candidates: [] },
  op: { candidates: TARGETS },
  deop: { candidates: TARGETS },
  kick: { candidates: TARGETS },
  ban: { candidates: TARGETS },
  'ban-ip': { candidates: [{ token: '192.168.1.10', hint: '要封禁的 IP（示例）' }] },
  banlist: {
    candidates: [
      { token: 'players', hint: '玩家封禁列表' },
      { token: 'ips', hint: 'IP 封禁列表' },
    ],
  },
  pardon: { candidates: TARGETS },
  'pardon-ip': { candidates: [{ token: '192.168.1.10', hint: '要解封的 IP（示例）' }] },
  whitelist: {
    candidates: [
      { token: 'add 玩家名', hint: '加入白名单（示例）' },
      { token: 'remove 玩家名', hint: '移出白名单（示例）' },
      { token: 'list', hint: '查看白名单' },
      { token: 'on', hint: '启用白名单' },
      { token: 'off', hint: '关闭白名单' },
    ],
  },
  'save-all': { candidates: [] },
  'save-off': { candidates: [] },
  'save-on': { candidates: [] },
  stop: { candidates: [] },
  setidletimeout: { candidates: [{ token: '5', hint: '5 分钟无操作踢出' }] },
  publish: { candidates: [] },
  transfer: { candidates: [{ token: 'localhost 25565', hint: '转移到本地 25565 端口（示例）' }] },
  version: { candidates: [] },

  perf: {
    candidates: [
      { token: 'start', hint: '开始记录 10 秒' },
      { token: 'stop', hint: '提前结束' },
    ],
  },
  jfr: {
    candidates: [
      { token: 'start', hint: '开始 JFR 记录' },
      { token: 'stop', hint: '停止' },
      { token: 'dump', hint: '导出记录' },
    ],
  },
  debug: {
    candidates: [
      { token: 'start', hint: '开始调试会话' },
      { token: 'stop', hint: '结束调试会话' },
    ],
  },
  fetchprofile: { candidates: [{ token: 'Notch', hint: '玩家名（示例）' }] },

  experience: {
    candidates: [
      { token: 'add', hint: '增加经验' },
      { token: 'set', hint: '设置经验' },
      { token: 'query', hint: '查询经验' },
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
    token: `1[custom_name='{"text":"自定义名"}']`,
    hint: '自定义名称（SNBT 文本组件）',
  },
  {
    token: `1[lore=['{"text":"第一行说明"}','{"text":"第二行"}']]`,
    hint: '自定义描述（多行用逗号分隔）',
  },
  {
    token: `1[enchantments={levels:{"minecraft:sharpness":5}}]`,
    hint: '直接附带附魔（锋利 V）',
  },
  {
    token: `1[enchantments={levels:{"minecraft:protection":4,"minecraft:unbreaking":3}}]`,
    hint: '多个附魔（保护 IV + 耐久 III）',
  },
  { token: '1[unbreakable={}]', hint: '无法损坏' },
  { token: '1[rarity="epic"]', hint: '稀有度（epic 史诗）' },
  { token: '1[dyed_color={rgb:16711680}]', hint: '染色（皮革盔甲，红色）' },
  { token: '1[damage=10]', hint: '已损耗值（设置耐久消耗）' },
  { token: '1[max_damage=1000]', hint: '最大耐久 1000' },
  { token: '1[attribute_modifiers=[]]', hint: '清空属性修饰符' },
  { token: '64', hint: '只要数量，不加组件' },
];

/** 实体 NBT（summon 的最后一个参数） */
const ENTITY_NBT: Candidate[] = [
  { token: '~ ~ ~ {NoAI:1b}', hint: '不活动（木桩人）' },
  { token: '~ ~ ~ {NoAI:1b,Silent:1b}', hint: '不活动 + 静音' },
  { token: '~ ~ ~ {PersistenceRequired:1b}', hint: '不会自然消失' },
  { token: '~ ~ ~ {Invulnerable:1b}', hint: '无敌' },
  { token: '~ ~ ~ {NoGravity:1b}', hint: '不受重力（浮空）' },
  { token: '~ ~ ~ {Glowing:1b}', hint: '发光描边' },
  { token: `~ ~ ~ {CustomName:'{"text":"守卫"}',CustomNameVisible:1b}`, hint: '头顶显示名字' },
  { token: '~ ~ ~ {Health:5.0f}', hint: '初始血量 5' },
  {
    token: '~ ~ ~ {ArmorItems:[{},{},{},{id:"minecraft:diamond_helmet",count:1}]}',
    hint: '穿装备（钻石头盔）',
  },
  {
    token: '~ ~ ~ {HandItems:[{id:"minecraft:diamond_sword",count:1},{}]}',
    hint: '手持物品（钻石剑）',
  },
  { token: '~ ~ ~', hint: '只要坐标，不加 NBT' },
];

/** 方块 NBT（setblock / fill 的最后一个参数） */
const BLOCK_NBT: Candidate[] = [
  {
    token: '{Items:[{Slot:0b,id:"minecraft:diamond",count:64}]}',
    hint: '容器内容：64 个钻石（箱子/桶）',
  },
  {
    token: '{Items:[{Slot:0b,id:"minecraft:golden_apple",count:16}]}',
    hint: '容器内容：16 个金苹果',
  },
  { token: '{Lock:"钥匙"}', hint: '上锁（需要同名物品才能打开）' },
  { token: `{CustomName:'{"text":"宝箱"}'}`, hint: '自定义容器名称' },
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

/** 全量候选索引（带上级路径），用于中文检索 */
export const ALL_CANDIDATES: IndexedCandidate[] = [
  ...ROOT_CANDIDATES.map((c) => ({ ...c, parent: '' })),
  ...Object.entries(COMMAND_TREE).flatMap(([parent, node]) =>
    node.candidates.map((c) => ({ ...c, parent })),
  ),
];

/** 中文/英文关键词检索：匹配 token 或中文说明 */export function searchCandidates(keyword: string, limit = 60): IndexedCandidate[] {
  const key = keyword.trim().toLowerCase();
  if (!key) return [];
  const hits = ALL_CANDIDATES.filter(
    (c) => c.token.toLowerCase().includes(key) || c.hint.toLowerCase().includes(key),
  );
  // 去重（同一个 token + hint 可能在多个父级下出现）
  const seen = new Set<string>();
  const unique: IndexedCandidate[] = [];
  for (const hit of hits) {
    const id = `${hit.parent}|${hit.token}|${hit.hint}`;
    if (seen.has(id)) continue;
    seen.add(id);
    unique.push(hit);
    if (unique.length >= limit) break;
  }
  return unique;
}

/** 给 Ctrl+Alt+Q 速查小窗用的扁平候选表（Python 侧检索用） */
export function buildPaletteEntries(): { token: string; hint: string; parent: string }[] {
  return ALL_CANDIDATES.map((c) => ({ token: c.token, hint: c.hint, parent: c.parent }));
}

/** 所有合法的指令前缀（含"没有后续候选"的完整指令），速查窗用来区分"完整"与"无效" */
export const COMMAND_NODES: string[] = Object.keys(COMMAND_TREE);
