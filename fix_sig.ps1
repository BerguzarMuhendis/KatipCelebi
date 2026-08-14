$files = @(
  ".gitignore","CONTRIBUTING.md","KatipCelebi.spec","LICENSE","README.md","app.spec",
  "pytest.ini","requirements.txt","scripts/build-linux-arch.sh","scripts/build-linux-deb.sh",
  "scripts/build-linux-rpm.sh","assets/lang/en.json","assets/lang/es.json","assets/lang/fr.json",
  "assets/lang/ru.json","assets/lang/tr.json","assets/lang/zh.json","assets/styles/default.qss",
  "src/app.py","src/app_shell.py","src/books/add.py","src/books/card.py","src/books/covers.py",
  "src/books/detail.py","src/books/excel.py","src/books/excel_io.py","src/books/facts.py",
  "src/books/filters.py","src/books/flowlayout.py","src/books/grid.py","src/books/import_worker.py",
  "src/books/lending_panel.py","src/books/library_page.py","src/books/model.py",
  "src/books/openlibrary/__init__.py","src/books/openlibrary/client.py","src/books/openlibrary/parser.py",
  "src/books/personal.py","src/books/reading.py","src/books/store.py","src/books/tags.py",
  "src/people/model.py","src/people/page.py","src/people/store.py","src/settings/page.py",
  "src/settings/page_impl.py","src/settings/relocate.py","src/shared/config.py",
  "src/shared/credentials.py","src/shared/icons.py","src/shared/logs.py","src/shared/palette.py",
  "src/shared/paths.py","src/shared/settings_helpers.py","src/shared/shape.py",
  "src/shared/storage.py","src/shared/texts.py","src/shared/theme/__init__.py",
  "src/shared/theme/core.py","src/shared/theme/preview.py","src/shared/theme/qss.py",
  "src/shared/update.py","src/stats/goals.py","src/stats/page.py","src/stats/summary.py",
  "tests/test_e2e.py","tests/test_excel_io.py","tests/test_model.py","tests/test_paths.py"
)

$sig = "01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001"
$preMap = @{".py"="# ";".sh"="# ";".spec"="# ";".ini"="# ";".txt"="# ";".md"="<!-- ";".qss"="/* ";".json"="// "}
$sufMap = @{".md"=" -->";".html"=" -->";".qss"=" */";".css"=" */"}
$esc = [regex]::Escape($sig)

foreach($f in $files){
  if(Test-Path $f){
    $c = Get-Content $f -Raw
    # Remove all trailing signature patterns
    $pattern = "(?s)\s*(?:#|//|/\*|<!--)?\s*" + $esc + "\s*(?:\*/|-->)?\s*$"
    while($c -match $pattern){
      $c = $c -replace $pattern, ""
    }
    $ext = [IO.Path]::GetExtension($f).ToLower()
    $pre = $preMap[$ext]; if(-not $pre){$pre="# "}
    $suf = $sufMap[$ext]; if(-not $suf){$suf=""}
    Set-Content $f ($c.TrimEnd() + "`n" + $pre + $sig + $suf)
    Write-Host "Fixed: $f"
  }
}