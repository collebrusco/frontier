# just so I don't forget it
.PHONY: exe

exe: frontier_launcher.py
	python -m PyInstaller --onefile --noconsole --add-data "img/icon.png;." --icon "img/icon.png" frontier_launcher.py

clean:
	rm frontier_launcher.spec
	rm -rf build
	rm -rf dist
