#!/bin/bash

# Create quick index.html from pictures directory
# Silas S. Brown - public domain - v1.3

# use with (e.g.) webfsd -f index.html   # port 8000

# or use --md to create README.md for GitHub/GitLab
# or use --epub to create epub (with Calibre) (use subdirectories for chapters)

if [ "$1" == --md ] ; then Out=README.md; else Out=index.html; fi
if [ -e "$Out" ]; then
    echo "Error: $Out already exists"
    exit 1
fi
if [ "$Out" == index.html ] ; then echo '<html><body style="overflow-x:hidden;margin:0">' > "$Out"; fi
file -- *|grep '^[^.\"$]*: .*image data'|sed -Ee 's/([^:]+): *([^ ]*) image data.*/mv -- "\1" "\1.\2"/'|sh # rename files with no extension, e.g. from /storage/emulated/0/Android/data/com.sec.android.gallery3d/files/.Trash if recovering from Samsung 'recycle bin'
if [ "$Out" == index.html ] ; then find -s . -type d -depth 1 -exec /bin/bash -c "cd '{}' && "'"'"$(readlink -f "$0")"'"'" >/dev/null && echo '<p><a href="'"'"{}/index.html"'"'">{}</a></p>'|sed -e s,[.]/,,g" ';' >> "$Out"; fi # subdirectories (TODO: could do an md version of this) or for ebook-convert
for F in *; do case $F in *.jpg|*.JPG|*.jpeg|*.JPEG|*.png|*.PNG)
    case "$Out" in
        (README.md) echo '!'"[]($F)" ;;
        (index.html)
  case "$(exiftool -list -- "$F"|grep ^Orientation|sed -e 's/.*: //')" in
      ("Rotate 90 CW")
          echo "<div style=\"display:table\"><div style=\"padding:50% 0;height:0\"><img style=\"width:auto;height:calc(100vw - 31px);display:block;transform-origin: top left; transform: rotate(90deg) translate(0,-100%) ; margin-top: -50%; image-orientation: none\" src=\"$F\"></div></div>"
          ;;
      # for 270 CW or 90 CCW, use rotate(-90deg) translate(-100%) : https://stackoverflow.com/questions/16301625
      # The image-orientation part is to turn off the automatic EXIF reading in newer browsers, because we're supplying it for older browsers
      (*)
          echo "<img style=\"width:100%; height:auto;\" src=\"$F\">"
          ;;
      esac # rotated or not
      ;;
    esac # md / html
  echo "$F" >&2
;; esac; done >> "$Out"
if [ "$1" == --epub ] ; then
ebook-convert index.html pictures.epub --dont-split-on-page-breaks --no-default-epub-cover --title pictures
else du -h "$Out"; fi
