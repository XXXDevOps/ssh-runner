.PHONY: build release
tmpdirroot = /tmp/dj_ci
tmpdir2 = $(tmpdirroot)/release

script = ./script

all: clean build

build:
	./$(script)/dj_build.sh
	cp -r ./build/venv ./dist/
	cp script/start_dj.sh ./dist/
	cp script/stop_dj.sh ./dist/
clean:
	rm -rf build
	rm -rf dist
release: clean
	mkdir -p /tmp/dj/release/bin/
	mkdir -p /tmp/dj/release/conf/
	cp davyJones.py /tmp/dj/release/bin/
	cp connection_data.py /tmp/dj/release/bin/
	cp -r ./build/packages/*  /tmp/dj/release/bin/
	cp -r ./dist/* /tmp/dj/release/bin/
	cp -r /tmp/dj/release ./
	rm -rf /tmp/dj/release
