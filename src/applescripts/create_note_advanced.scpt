on run {noteTitle, noteBody, targetFolder}
    tell application "Notes"
        activate
        if targetFolder is not "" then
            -- Check if the folder exists
            if not (exists folder targetFolder) then
                -- If not, create it
                make new folder with properties {name:targetFolder}
            end if
            
            -- Create the note in the specified folder
            tell folder targetFolder
                make new note with properties {name:noteTitle, body:noteBody}
            end tell
        else
            -- Create the note in the default location (All iCloud or On My Mac)
            make new note with properties {name:noteTitle, body:noteBody}
        end if
        
        -- Optional: bring Notes to front to see the result
        -- activate
    end tell
    return "Note titled '" & noteTitle & "' created successfully in folder '" & targetFolder & "'."
end run