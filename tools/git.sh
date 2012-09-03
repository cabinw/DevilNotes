mv ../../021_devilnotes_public/.git ../../021_devilnotes_public_git
rm -rf ../../021_devilnotes_public/
cp -Rv ../ ../../021_devilnotes_public
rm -rf ../../021_devilnotes_public/.git
mv ../../021_devilnotes_public_git ../../021_devilnotes_public/.git
echo '' >> ../../021_devilnotes_public/.gitignore
echo 'tools/git.sh' >> ../../021_devilnotes_public/.gitignore
echo 'config.py' >> ../../021_devilnotes_public/.gitignore
rm -f ../../021_devilnotes_public/static/favicon.ico
