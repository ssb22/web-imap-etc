#!/bin/bash

# Create quick index.html from pictures directory
# Silas S. Brown - public domain - v1.61

# use with (e.g.) webfsd -f index.html   # port 8000

# or use --md to create README.md for GitHub/GitLab
# or use --epub to create epub (with Calibre) (use subdirectories for chapters)

if [ "$1" == --md ] ; then Out=README.md; else Out=index.html; fi
if [ -e "$Out" ]; then
    echo "Error: $Out already exists"
    exit 1
fi
if [ "$Out" == index.html ] ; then echo '<html><body style="overflow-x:hidden;margin:0">' > "$Out"; fi
export LC_ALL=C # stabilise sorts across platforms
file -- *|grep '^[^.\"$]*: .*image data'|sed -Ee 's/([^:]+): *([^ ]*) image data.*/mv -- "\1" "\1.\2"/'|sh # rename files with no extension, e.g. from /storage/emulated/0/Android/data/com.sec.android.gallery3d/files/.Trash if recovering from Samsung 'recycle bin'
# BSD 'find' has -s to do it in sorted order, GNU/Linux doesn't, so sort o/p after:
if [ "$Out" == index.html ] ; then find . -maxdepth 1 -type d -exec /bin/bash -c "cd '{}' && "'"'"$(readlink -f "$0")"'"'" >/dev/null && mv index.html '{}'.html && echo '<p><a href="'"'"{}/{}.html"'"'">{}</a></p>'|sed -e s,[.]/,,g" ';' | sort >> "$Out"; fi # subdirectories (TODO: could do an md version of this) or for ebook-convert (using non-index.html for that so zip listing is clearer)
for F in *; do case $F in *.jpg|*.JPG|*.jpeg|*.JPEG|*.png|*.PNG)
    case "$Out" in
        (README.md) echo '!'"[]($F)" ;;
        (index.html)
  case "$(exiftool -- "$F"|grep ^Orientation|sed -e 's/.*: //')" in
      ("Rotate 90 CW")
          echo "<div style=\"display:table\"><div style=\"padding:50% 0;height:0\"><img style=\"width:auto;height:calc(100vw - 31px);display:block;transform-origin: top left; transform: rotate(90deg) translate(0,-100%) ; margin-top: -50%; image-orientation: none\" src=\"$F\" width=\"$(exiftool -- "$F"|grep ^Image.Width|sed -e 's/.* //')\" height=\"$(exiftool -- "$F"|grep ^Image.Height|sed -e 's/.* //')\"></div></div>"
          ;;
      # for 270 CW or 90 CCW, use rotate(-90deg) translate(-100%) : https://stackoverflow.com/questions/16301625
      # The image-orientation part is to turn off the automatic EXIF reading in newer browsers, because we're supplying it for older browsers
      (*)
          echo "<img style=\"width:100%; height:auto;\" src=\"$F\" width=\"$(exiftool -- "$F"|grep ^Image.Width|sed -e 's/.* //')\" height=\"$(exiftool -- "$F"|grep ^Image.Height|sed -e 's/.* //')\">"
          ;;
      esac # rotated or not
      ;;
    esac # md / html
  echo "$F" >&2
;; esac; done >> "$Out"
if [ "$1" == --epub ] ; then
mv index.html toc.xhtml
ebook-convert toc.xhtml pictures.epub --dont-split-on-page-breaks --no-default-epub-cover --title pictures
mkdir .p0 && cd .p0 && unzip ../pictures.epub && rm ../pictures.epub && zip -9r ../pictures.epub -- * && cd .. && rm -rf .p0 # ensure files sorted
else du -h "$Out"; fi
