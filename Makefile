APP_NAME=my_kivy_app
BUILD_IMAGE=kivy/buildozer
HOME_DIR=$(HOME)
PROJECT_DIR=$(shell pwd)

android:
	docker run --rm \
		-v $(HOME)/.buildozer:/home/user/.buildozer \
		-v $(PWD):/home/user/hostcwd \
		-w /home/user/hostcwd \
		kivy/buildozer \
		android debug

formatar_codigo:
	black main.py
	black app/
	isort main.py
	isort app/