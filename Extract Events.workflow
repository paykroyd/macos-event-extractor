<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>521.1</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMApplication</key>
				<dict>
					<key>CFBundleIdentifier</key>
					<string>com.apple.automator.RunShellScript</string>
				</dict>
				<key>AMParameterProperties</key>
				<dict>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>inputMethod</key>
					<integer>1</integer>
					<key>shell</key>
					<string>/bin/bash</string>
					<key>source</key>
					<string>#!/bin/bash

# Event Extractor Service - Called from Automator
# Get the directory where the workflow is located
WORKFLOW_DIR="$(dirname "$0")"

# Try to find the script directory
SCRIPT_DIR=""

# First, try relative to workflow
if [ -f "$WORKFLOW_DIR/extract_events_service.sh" ]; then
    SCRIPT_DIR="$WORKFLOW_DIR"
elif [ -f "$WORKFLOW_DIR/../extract_events_service.sh" ]; then
    SCRIPT_DIR="$WORKFLOW_DIR/.."
elif [ -f "$HOME/extract_event/extract_events_service.sh" ]; then
    SCRIPT_DIR="$HOME/extract_event"
elif [ -f "$HOME/Documents/extract_event/extract_events_service.sh" ]; then
    SCRIPT_DIR="$HOME/Documents/extract_event"
elif [ -f "$HOME/Desktop/extract_event/extract_events_service.sh" ]; then
    SCRIPT_DIR="$HOME/Desktop/extract_event"
fi

# If we found the script directory, run it
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/extract_events_service.sh" ]; then
    cd "$SCRIPT_DIR"
    exec ./extract_events_service.sh
else
    # Show error if script not found
    osascript -e 'display alert "Event Extractor Error" message "Cannot find extract_events_service.sh script. Please ensure the extract_event folder is in your home directory, Documents, or Desktop." buttons {"OK"} default button "OK"'
    exit 1
fi</string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.automator.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>F8B5B9E8-8A5A-4B3C-9D2E-1F7C6A9B8D3E</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>2C4D6F8A-3B5C-4D7E-8F9A-1B2C3D4E5F6A</string>
				<key>UUID</key>
				<string>A1B2C3D4-E5F6-7A8B-9C0D-1E2F3A4B5C6D</string>
				<key>UnlocalizedApplications</key>
				<array>
					<string>Automator</string>
				</array>
				<key>arguments</key>
				<dict>
					<key>0</key>
					<dict>
						<key>default value</key>
						<integer>0</integer>
						<key>name</key>
						<string>inputMethod</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>0</string>
					</dict>
					<key>1</key>
					<dict>
						<key>default value</key>
						<string>/bin/sh</string>
						<key>name</key>
						<string>shell</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>1</string>
					</dict>
					<key>2</key>
					<dict>
						<key>default value</key>
						<string></string>
						<key>name</key>
						<string>source</string>
						<key>required</key>
						<string>0</string>
						<key>type</key>
						<string>0</string>
						<key>uuid</key>
						<string>2</string>
					</dict>
				</dict>
				<key>isViewVisible</key>
				<true/>
				<key>location</key>
				<string>449.000000:316.000000</string>
				<key>nibPath</key>
				<string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib</string>
			</dict>
			<key>isViewVisible</key>
			<true/>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>applicationBundleID</key>
		<string>com.apple.automator.workflow</string>
		<key>applicationBundleIDsByPath</key>
		<dict/>
		<key>applicationPaths</key>
		<array/>
		<key>inputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>outputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>presentationMode</key>
		<integer>15</integer>
		<key>processesInput</key>
		<false/>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceOutputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceApplications</key>
		<array>
			<string>Finder</string>
			<string>TextEdit</string>
			<string>Safari</string>
			<string>Mail</string>
			<string>Pages</string>
			<string>Notes</string>
		</array>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
