# just so I don't forget it
.PHONY: exe

exe: installer_updater_src.py
	python -m PyInstaller --onefile --noconsole --add-data "img/icon.png;." --icon "img/icon.png" installer_updater_src.py

clean:
	rm installer_updater_src.spec
	rm -rf build
	rm -rf dist
