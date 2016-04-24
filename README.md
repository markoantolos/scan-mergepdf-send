# scan-mergepdf-send
Python script that merges recently scanned documents into a single PDF file and (optionally) creates a draft email (GMail API) with PDF attached for opening in GMail (browser) or send it directly from script. Uses fuzzy matching against your GMail contacts for ease of use. Script also moves the scanned files from original directory to archive to prevent bloat.

Currently works with PDF scans but planning to support JPEGs.
Also planning for compression support and ID card scans (and more...)
