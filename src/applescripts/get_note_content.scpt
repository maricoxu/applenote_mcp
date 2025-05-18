-- get_note_content.scpt
-- 接收参数: targetTitle_param, targetFolder_param (可选)
-- 功能: 获取指定唯一笔记的 body 内容。

on run {targetTitle_param, targetFolder_param}
    set targetTitle to targetTitle_param as string
    set targetFolder to targetFolder_param as string

    if targetTitle is equal to "" then
        return "错误：笔记标题不能为空。"
    end if

    tell application "Notes"
        activate

        set searchScope to {}
        set scopeDescription to ""

        if targetFolder is not equal to "" then
            if not (exists folder targetFolder) then
                return "错误：指定的文件夹 '" & targetFolder & "' 不存在。"
            end if
            set searchScope to notes of folder targetFolder
            set scopeDescription to "文件夹 '" & targetFolder & "'"
        else
            set searchScope to every note
            set scopeDescription to "所有笔记"
        end if

        set foundNotes to {}
        repeat with aNote in searchScope
            if name of aNote is equal to targetTitle then
                set end of foundNotes to aNote
            end if
        end repeat

        set numFound to count of foundNotes
        if numFound is equal to 0 then
            return "错误：在 " & scopeDescription & " 中未找到标题为 '" & targetTitle & "' 的笔记。"
        else if numFound is equal to 1 then
            set theNote to item 1 of foundNotes
            try
                return body of theNote
            on error errMsg number errNum
                return "错误：读取笔记 '" & targetTitle & "' 内容时发生错误：" & errMsg
            end try
        else -- numFound > 1
            return "错误：在 " & scopeDescription & " 中找到 " & numFound & " 个标题为 '" & targetTitle & "' 的笔记。请确保标题唯一或指定更精确的文件夹。"
        end if
    end tell
end run