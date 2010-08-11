<?php

/**
 * Script to configure dogbark user based on 'u' parameter
 * Usage: Set DOGBARK_HTML define to correct file. Also make
 *        sure that PHP-files are prioritized over HTML files
 *        if dogbark HTML file is named index.html
 */

define("DOGBARK_HTML", "dogbark.html");
define("CONFIG_STR", "<!-- [PARAMS] //-->");
define("BASE_STR", "<!-- [BASE] //-->");
define("USER_PARAM", "u");

// Any particular user requested?
$user = ($_REQUEST[USER_PARAM]);
if(empty($user)) {
  echo file_get_contents(DOGBARK_HTML);
  die();
}

// Create site root
$site = "http://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']);
if(substr($site, -1) != "/")
{
   $site .= "/";
}

//Add base for content
$content = file_get_contents(DOGBARK_HTML);
$REPLACE_STR = "<base href='".$site."'>";
$content = str_replace(BASE_STR, $REPLACE_STR, $content);

//Insert Javascript to select dog
$REPLACE_STR = 
"<script type='text/javascript'>
  if(Config.defaultUser) { Config.defaultUser = '".$user."'; }
</script>";

echo str_replace(CONFIG_STR, $REPLACE_STR, $content);


?>