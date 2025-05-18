on run {noteTitleToDelete, targetFolder}
    tell application "Notes"
        activate
        set notesDeletedCount to 0
        if targetFolder is not "" then
            if exists folder targetFolder then
                tell folder targetFolder
                    set notesToSearch to a reference to every note
                    repeat with i from (count of notesToSearch) to 1 by -1
                        set aNote to item i of notesToSearch
                        if name of aNote is noteTitleToDelete then
                            delete aNote
                            set notesDeletedCount to notesDeletedCount + 1
                        end if
                    end repeat
                end tell
                return "Deleted " & notesDeletedCount & " note(s) titled '" & noteTitleToDelete & "' from folder '" & targetFolder & "'."
            else
                return "Info: Folder '" & targetFolder & "' not found. No notes deleted."
            end if
        else
            set notesToSearchInAll to a reference to every note
            repeat with i from (count of notesToSearchInAll) to 1 by -1
                set aNoteInAll to item i of notesToSearchInAll
                if name of aNoteInAll is noteTitleToDelete and (container of aNoteInAll is equal to account "iCloud" or container of aNoteInAll is equal to account "On My Mac" or (exists folder "Notes" of account "iCloud" and container of aNoteInAll is equal to folder "Notes" of account "iCloud")) then
                    delete aNoteInAll
                    set notesDeletedCount to notesDeletedCount + 1
                end if
            end repeat
            return "Deleted " & notesDeletedCount & " note(s) titled '" & noteTitleToDelete & "' from default location (use with caution)."
        end if
    end tell
end run
