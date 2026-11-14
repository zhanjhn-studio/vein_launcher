<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, X-Author, X-User');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$configFile = '/www/_private/vl-posts.php';
if (!is_file($configFile)) {
    http_response_code(500);
    echo json_encode(['error' => ['code' => 'not_configured', 'message' => 'server config missing']], JSON_UNESCAPED_UNICODE);
    exit;
}
$cfg = require $configFile;

try {
    $pdo = new PDO($cfg['dsn'], $cfg['user'], $cfg['pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => ['code' => 'db_unavailable', 'message' => 'database unavailable']], JSON_UNESCAPED_UNICODE);
    exit;
}

function respond(array $data, int $code = 200): void
{
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function fail(string $message, int $code = 400, string $error = 'bad_request'): void
{
    respond(['error' => ['code' => $error, 'message' => $message]], $code);
}

function body(): array
{
    $raw = file_get_contents('php://input') ?: '';
    if ($raw === '') {
        return $_POST ?: [];
    }
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

function tags_for(PDO $pdo, array $ids): array
{
    if (!$ids) {
        return [];
    }
    $in = implode(',', array_fill(0, count($ids), '?'));
    $stmt = $pdo->prepare("SELECT post_id, t.name FROM post_tags pt JOIN tags t ON t.id = pt.tag_id WHERE pt.post_id IN ($in)");
    $stmt->execute(array_values($ids));
    $map = [];
    foreach ($stmt->fetchAll() as $row) {
        $map[(int)$row['post_id']][] = $row['name'];
    }
    return $map;
}

function excerpt(string $text, int $limit = 160): string
{
    $text = trim(preg_replace('/\s+/u', ' ', strip_tags($text)));
    return mb_strlen($text, 'UTF-8') > $limit ? mb_substr($text, 0, $limit, 'UTF-8') . '…' : $text;
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$path = preg_replace('#^/api#', '', $path) ?: '/';
$segments = array_values(array_filter(explode('/', $path), static fn($s) => $s !== ''));

$ip = $_SERVER['REMOTE_ADDR'] ?? '';
$ua = $_SERVER['HTTP_USER_AGENT'] ?? '';
$ipHash = substr(sha1($ip . '|' . $ua), 0, 16);
$userKey = trim((string)($_SERVER['HTTP_X_USER'] ?? '')) ?: 'ip-' . $ipHash;

// GET /api/health
if ($method === 'GET' && (($segments[0] ?? '') === 'health' || $segments === [])) {
    respond([
        'ok' => true,
        'service' => 'vein-posts',
        'version' => '1.0.0',
        'time' => date('c'),
    ]);
}

// GET /api/tags
if ($method === 'GET' && ($segments[0] ?? '') === 'tags' && count($segments) === 1) {
    $rows = $pdo->query(
        'SELECT t.name, COUNT(pt.post_id) AS count
         FROM tags t LEFT JOIN post_tags pt ON pt.tag_id = t.id
         GROUP BY t.id, t.name ORDER BY count DESC, t.id ASC'
    )->fetchAll();
    respond(['items' => array_map(static fn($r) => ['name' => $r['name'], 'count' => (int)$r['count']], $rows)]);
}

// GET /api/posts
if ($method === 'GET' && ($segments[0] ?? '') === 'posts' && count($segments) === 1) {
    $limit = min(50, max(1, (int)($_GET['limit'] ?? 20)));
    $page = max(1, (int)($_GET['page'] ?? 1));
    $sort = ($_GET['sort'] ?? 'hot') === 'new' ? 'new' : 'hot';
    $tag = trim((string)($_GET['tag'] ?? ''));

    $where = '';
    $params = [];
    if ($tag !== '') {
        $where = 'WHERE EXISTS (SELECT 1 FROM post_tags pt JOIN tags t ON t.id = pt.tag_id WHERE pt.post_id = p.id AND t.name = ?)';
        $params[] = $tag;
    }
    $order = $sort === 'new'
        ? 'p.created_at DESC, p.id DESC'
        : '(p.likes / POW(TIMESTAMPDIFF(HOUR, p.created_at, NOW()) + 2, 1.5)) DESC, p.created_at DESC';

    $countStmt = $pdo->prepare("SELECT COUNT(*) FROM posts p $where");
    $countStmt->execute($params);
    $total = (int)$countStmt->fetchColumn();

    $sql = "SELECT p.id, p.title, p.content, p.author_name, p.likes, p.created_at,
                   (p.likes / POW(TIMESTAMPDIFF(HOUR, p.created_at, NOW()) + 2, 1.5)) AS hot_score
            FROM posts p $where ORDER BY $order LIMIT $limit OFFSET " . (($page - 1) * $limit);
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();
    $tagMap = tags_for($pdo, array_map(static fn($r) => (int)$r['id'], $rows));

    $items = array_map(static function (array $r) use ($tagMap): array {
        return [
            'id' => (int)$r['id'],
            'title' => $r['title'],
            'excerpt' => excerpt((string)$r['content']),
            'author_name' => $r['author_name'],
            'likes' => (int)$r['likes'],
            'tags' => $tagMap[(int)$r['id']] ?? [],
            'created_at' => str_replace(' ', 'T', $r['created_at']),
            'hot_score' => round((float)$r['hot_score'], 4),
        ];
    }, $rows);

    respond([
        'items' => $items,
        'page' => $page,
        'limit' => $limit,
        'total' => $total,
        'has_more' => $page * $limit < $total,
    ]);
}

// GET /api/posts/{id}
if ($method === 'GET' && ($segments[0] ?? '') === 'posts' && isset($segments[1]) && ctype_digit((string)$segments[1]) && count($segments) === 2) {
    $postId = (int)$segments[1];
    $stmt = $pdo->prepare('SELECT id, title, content, author_name, likes, created_at FROM posts WHERE id = ?');
    $stmt->execute([$postId]);
    $row = $stmt->fetch();
    if (!$row) {
        fail('post not found', 404, 'not_found');
    }
    $tagMap = tags_for($pdo, [$postId]);
    respond([
        'id' => (int)$row['id'],
        'title' => $row['title'],
        'content' => $row['content'],
        'author_name' => $row['author_name'],
        'likes' => (int)$row['likes'],
        'tags' => $tagMap[$postId] ?? [],
        'created_at' => str_replace(' ', 'T', $row['created_at']),
    ]);
}

// POST /api/posts
if ($method === 'POST' && ($segments[0] ?? '') === 'posts' && count($segments) === 1) {
    $data = body();
    $title = trim((string)($data['title'] ?? ''));
    $content = trim((string)($data['content'] ?? ''));
    $tags = $data['tags'] ?? [];
    $author = trim((string)($data['author'] ?? ($_SERVER['HTTP_X_AUTHOR'] ?? '')));

    if (mb_strlen($title, 'UTF-8') < 4 || mb_strlen($title, 'UTF-8') > 120) {
        fail('title must be 4-120 characters', 422, 'invalid_title');
    }
    if (mb_strlen($content, 'UTF-8') < 2 || mb_strlen($content, 'UTF-8') > 20000) {
        fail('content must be 2-20000 characters', 422, 'invalid_content');
    }
    if (mb_strlen($author, 'UTF-8') < 1 || mb_strlen($author, 'UTF-8') > 20) {
        fail('author must be 1-20 characters', 422, 'invalid_author');
    }
    $author = preg_replace('/[^\p{L}\p{N}_\- ]/u', '', $author) ?: '匿名';
    if (!is_array($tags)) {
        $tags = [];
    }
    $tags = array_slice(array_values(array_unique(array_filter(array_map(
        static fn($t) => trim((string)$t),
        $tags
    )))), 0, 5);
    foreach ($tags as $tag) {
        if (mb_strlen($tag, 'UTF-8') > 32) {
            fail('tag too long', 422, 'invalid_tag');
        }
    }

    // 限流：同一 IP 每小时最多 3 篇
    $now = date('Y-m-d H:i:s');
    $stmt = $pdo->prepare('SELECT window_start, count FROM rate_limits WHERE ip_hash = ?');
    $stmt->execute([$ipHash]);
    $rl = $stmt->fetch();
    $count = 0;
    if ($rl) {
        $count = (time() - strtotime($rl['window_start'])) < 3600 ? (int)$rl['count'] : 0;
    }
    if ($count >= 3) {
        fail('too many posts, try again later', 429, 'rate_limited');
    }
    $stmt = $pdo->prepare('INSERT INTO rate_limits (ip_hash, window_start, count) VALUES (?, ?, 1)
        ON DUPLICATE KEY UPDATE window_start = IF(window_start < DATE_SUB(NOW(), INTERVAL 1 HOUR), VALUES(window_start), window_start),
        count = IF(window_start < DATE_SUB(NOW(), INTERVAL 1 HOUR), 1, count + 1)');
    $stmt->execute([$ipHash, $now]);

    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare('INSERT INTO posts (title, content, author_id, author_name, ip_hash) VALUES (?, ?, ?, ?, ?)');
        $stmt->execute([$title, $content, 'guest-' . $ipHash, $author, $ipHash]);
        $postId = (int)$pdo->lastInsertId();

        foreach ($tags as $tag) {
            $stmt = $pdo->prepare('INSERT INTO tags (name) VALUES (?) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)');
            $stmt->execute([$tag]);
            $tagId = (int)$pdo->lastInsertId();
            $stmt = $pdo->prepare('INSERT IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)');
            $stmt->execute([$postId, $tagId]);
        }
        $pdo->commit();
    } catch (Throwable $e) {
        $pdo->rollBack();
        fail('failed to save post', 500, 'save_failed');
    }

    respond([
        'id' => $postId,
        'title' => $title,
        'author_name' => $author,
        'tags' => $tags,
        'created_at' => date('c'),
    ], 201);
}

// POST /api/posts/{id}/like
if ($method === 'POST' && ($segments[0] ?? '') === 'posts' && isset($segments[1]) && ctype_digit((string)$segments[1]) && ($segments[2] ?? '') === 'like') {
    $postId = (int)$segments[1];
    $stmt = $pdo->prepare('SELECT id FROM posts WHERE id = ?');
    $stmt->execute([$postId]);
    if (!$stmt->fetch()) {
        fail('post not found', 404, 'not_found');
    }
    $data = body();
    $key = trim((string)($data['user_key'] ?? $userKey));
    if ($key === '' || strlen($key) > 64) {
        $key = $userKey;
    }
    $stmt = $pdo->prepare('INSERT IGNORE INTO likes (post_id, user_key) VALUES (?, ?)');
    $stmt->execute([$postId, $key]);
    $liked = $stmt->rowCount() > 0;
    $pdo->prepare('UPDATE posts SET likes = (SELECT COUNT(*) FROM likes WHERE post_id = ?) WHERE id = ?')->execute([$postId, $postId]);
    $stmt = $pdo->prepare('SELECT likes FROM posts WHERE id = ?');
    $stmt->execute([$postId]);
    respond(['liked' => $liked, 'likes' => (int)$stmt->fetchColumn()]);
}

fail('not found', 404, 'not_found');
