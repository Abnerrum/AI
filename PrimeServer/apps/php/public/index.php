<?php
header('Content-Type: text/html; charset=utf-8');
echo '<h1>PrimeServer — PHP funcionando!</h1>';
echo '<p>Versão do PHP: ' . htmlspecialchars(PHP_VERSION) . '</p>';
echo '<p>PDO SQLite: ' . (extension_loaded('pdo_sqlite') ? 'Ativo' : 'Inativo') . '</p>';
