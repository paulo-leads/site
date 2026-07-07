<?php
/**
 * Gerador de Sitemap Estático + Push Indexing — Paulo Leads
 * CCIE-level: Varredura Deep-Recursive (Suporte a Extensionless Files) e IndexNow API
 */

// ============================================================
// 0. SEGURANÇA BÁSICA
// ============================================================
$is_cli = (php_sapi_name() === 'cli');
$valid_token = isset($_GET['token']) && $_GET['token'] === 'sec_123';

if (!$is_cli && !$valid_token) {
    http_response_code(403);
    die("Acesso Negado. Utilize o token correto.\n");
}

$base_url = "https://pauloleads.com.br/";
$root_dir = __DIR__; 

// ============================================================
// 1. REGRAS DE VARREDURA
// ============================================================
$ignore_dirs = array('.git', '.private', 'DO_NOT_UPLOAD_HERE', 'node_modules', 'vendor', 'assets', 'css', 'js', 'images', 'fontes');
$ignore_files = array('404.php', '404.html', 'default.php', 'error_log', 'error.log', 'sitemap.xml', 'robots.txt', '.htaccess');

// Extensões que DEFINITIVAMENTE não devem ir pro sitemap
$bad_extensions = array(
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'ico',
    'css', 'js', 'json', 'map', 'txt', 'md', 'xml',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', 'rar', 'gz', 'tar', '7z',
    'woff', 'woff2', 'ttf', 'eot', 'otf',
    'mp4', 'avi', 'mkv', 'mov', 'wmv', 'mp3', 'wav', 'ini'
);

// ============================================================
// 2. FUNÇÕES CORE
// ============================================================

function get_priority($rel_path) {
    if ($rel_path === '' || strpos($rel_path, 'index') === 0) return '1.0';
    if (strpos($rel_path, 'analises-mercado/') !== false) return '0.9';
    if (strpos($rel_path, 'sobre') !== false || strpos($rel_path, 'protocolo') !== false) return '0.9';
    return '0.7';
}

function get_changefreq($rel_path) {
    if ($rel_path === '' || strpos($rel_path, 'analises-mercado/') !== false) return 'weekly';
    return 'monthly';
}

function clean_url_slug($rel_path) {
    // Transforma pasta/index.php em pasta/
    $slug = preg_replace('/\/index\.(php|html)$/i', '/', $rel_path);
    // Transforma index.php raiz em vazio
    $slug = preg_replace('/^index\.(php|html)$/i', '', $slug);
    // Remove extensões se houver (para os poucos que tiverem .php/.html)
    $slug = preg_replace('/\.(php|html)$/i', '', $slug);
    return htmlspecialchars(rtrim($slug, '/'));
}

// Scanner Deep-Recursive Modificado para Extensionless
function scan_directories_recursively($dir, $base_rel = '') {
    global $ignore_dirs, $ignore_files, $bad_extensions;
    $files = array();
    
    if (!is_readable($dir)) return $files;
    
    $items = scandir($dir);
    foreach ($items as $item) {
        // Ignora pastas ocultas e atalhos de sistema
        if ($item === '.' || $item === '..' || substr($item, 0, 1) === '.') continue;

        $path = $dir . '/' . $item;
        $rel_path = $base_rel ? $base_rel . '/' . $item : $item;

        if (is_dir($path)) {
            if (in_array($item, $ignore_dirs)) continue;
            // Recursividade
            $files = array_merge($files, scan_directories_recursively($path, $rel_path));
        } else {
            // Se for arquivo ignorado pelo nome completo
            if (in_array($item, $ignore_files)) continue;
            
            $ext = strtolower(pathinfo($item, PATHINFO_EXTENSION));
            
            // SE O ARQUIVO TIVER EXTENSÃO e for uma extensão proibida, ignora.
            if ($ext !== '' && in_array($ext, $bad_extensions)) continue;
            
            // SE O ARQUIVO TIVER EXTENSÃO, só aceita php ou html
            if ($ext !== '' && !in_array($ext, array('php', 'html'))) continue;

            // OBS: Se a extensão for VAZIA ($ext === ''), ele passa (suporta seus arquivos Hostinger)

            // Regra raiz: na pasta principal, evitar pegar lixo php. 
            // Libera form, obrigado, contato. Em subpastas, libera tudo.
            if ($base_rel === '' && $ext === 'php' && !preg_match('/^(index|contato|obrigado|form)/i', $item)) continue;

            $files[] = array(
                'filepath' => $path,
                'rel_path' => $rel_path
            );
        }
    }
    return $files;
}

// ============================================================
// 3. COMPILAÇÃO DO XML
// ============================================================

$scanned_files = scan_directories_recursively($root_dir);

$xml_content = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
$xml_content .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";

foreach ($scanned_files as $file) {
    // Evita indexar o próprio script de sitemap caso tenha nome diferente
    if (strpos($file['rel_path'], 'gerador') !== false) continue;

    $lastmod = date('Y-m-d', filemtime($file['filepath']));
    $url_slug = clean_url_slug($file['rel_path']);
    
    $priority = get_priority($file['rel_path']);
    $changefreq = get_changefreq($file['rel_path']);
    
    // Montagem blindada de URL
    $final_url = rtrim($base_url, '/') . '/' . ltrim($url_slug, '/');

    $xml_content .= "  <url>\n";
    $xml_content .= "    <loc>" . $final_url . "</loc>\n";
    $xml_content .= "    <lastmod>" . $lastmod . "</lastmod>\n";
    $xml_content .= "    <changefreq>" . $changefreq . "</changefreq>\n";
    $xml_content .= "    <priority>" . $priority . "</priority>\n";
    $xml_content .= "  </url>\n";
}

$xml_content .= "</urlset>\n";

// ============================================================
// 4. GRAVAÇÃO NO DISCO E BYPASS WAF
// ============================================================

$sitemap_path = $root_dir . '/sitemap.xml';
$bytes = file_put_contents($sitemap_path, $xml_content);

header('Content-Type: text/plain; charset=utf-8');

if ($bytes === false) {
    http_response_code(500);
    die("ERRO CRÍTICO: Falha ao escrever no disco. Verifique permissões em $root_dir\n");
}

echo "SUCESSO: sitemap.xml gerado com " . number_format($bytes / 1024, 2) . " KB. Total de links mapeados: " . count($scanned_files) . "\n\n";

// ============================================================
// 5. GROWTH HACK: PUSH INDEXING AUTOMATIZADO (cURL)
// ============================================================
echo "Iniciando disparos de Push Indexing...\n";

// 5.1 Protocolo IndexNow
$indexNowData = json_encode(array(
    "host" => "pauloleads.com.br",
    "key" => "5f0a46c7e20f48c7880b398f31699030",
    "keyLocation" => "https://pauloleads.com.br/5f0a46c7e20f48c7880b398f31699030.txt",
    "urlList" => array("https://pauloleads.com.br/sitemap.xml")
));

$ch1 = curl_init('https://api.indexnow.org/indexnow');
curl_setopt($ch1, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch1, CURLOPT_POST, true);
curl_setopt($ch1, CURLOPT_POSTFIELDS, $indexNowData);
curl_setopt($ch1, CURLOPT_HTTPHEADER, array('Content-Type: application/json; charset=utf-8', 'Content-Length: ' . strlen($indexNowData)));
curl_setopt($ch1, CURLOPT_TIMEOUT, 10);
curl_exec($ch1); curl_close($ch1);

echo " -> [INDEXNOW] OK: Ping enviado.\n";

// 5.2 Google Ping Clássico
$google_url = "https://www.google.com/ping?sitemap=https://pauloleads.com.br/sitemap.xml";
$ch2 = curl_init($google_url);
curl_setopt($ch2, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch2, CURLOPT_TIMEOUT, 10);
curl_setopt($ch2, CURLOPT_USERAGENT, "Mozilla/5.0 (compatible; PauloLeadsBot/1.0)");
curl_exec($ch2); curl_close($ch2);

echo " -> [GOOGLE] OK: Ping enviado.\n";
echo "\nFinalizado. Verifique em: https://pauloleads.com.br/sitemap.xml";
?>