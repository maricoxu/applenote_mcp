-- append_to_note.scpt
-- 接收参数: targetTitle_param, targetFolder_param, contentToAppend_param
-- 功能: 在指定文件夹（或所有笔记）中查找指定标题的笔记。
--       如果找到唯一一个，则将新内容追加到其末尾。
--       如果找不到或找到多个，则返回错误。

on run {targetTitle_param, targetFolder_param, contentToAppend_param}
    set targetTitle to targetTitle_param as string
    set targetFolder to targetFolder_param as string
    set contentToAppend to contentToAppend_param as string

    if targetTitle is equal to "" then
        return "错误：笔记标题不能为空。"
    end if

    tell application "Notes"
        activate -- 激活 Notes 应用，确保脚本可以交互

        set searchScope to {}
        set scopeDescription to ""

        if targetFolder is not equal to "" then
            if not (exists folder targetFolder) then
                return "错误：指定的文件夹 '" & targetFolder & "' 不存在。"
            end if
            set searchScope to notes of folder targetFolder
            set scopeDescription to "文件夹 '" & targetFolder & "'"
        else
            -- 如果没有指定文件夹，AppleScript 默认的 notes 对象会引用所有账户的笔记
            -- 这通常是期望的行为，即在所有笔记中查找
            set searchScope to every note
            set scopeDescription to "所有笔记"
        end if

        -- 查找匹配标题的笔记
        set foundNotes to {}
        repeat with aNote in searchScope
            if name of aNote is equal to targetTitle then
                set end of foundNotes to aNote
            end if
        end repeat

        -- 根据找到的笔记数量进行处理
        set numFound to count of foundNotes
        if numFound is equal to 0 then
            return "错误：在 " & scopeDescription & " 中未找到标题为 '" & targetTitle & "' 的笔记。"
        else if numFound is equal to 1 then
            set theNote to item 1 of foundNotes
            try
                set currentBody to body of theNote
                -- 追加内容。简单起见，我们用换行符连接。
                -- 如果内容是HTML，调用方应确保 contentToAppend 是合法的HTML片段，
                -- 或者我们在这里可以更智能地处理HTML拼接，例如用 <br>。
                -- 为保持通用性，先用换行符。如果需要HTML换行，调用方应传入带 <br> 的 contentToAppend。
                set newBody to currentBody & linefeed & contentToAppend
                set body of theNote to newBody
                return "成功：内容已追加到笔记 '" & targetTitle & "' (位于 " & scopeDescription & ")。"
            on error errMsg number errNum
                return "错误：追加内容到笔记 '" & targetTitle & "' 时发生错误：" & errMsg
            end try
        else -- numFound > 1
            return "错误：在 " & scopeDescription & " 中找到 " & numFound & " 个标题为 '" & targetTitle & "' 的笔记。请确保标题唯一或指定更精确的文件夹。"
        end if
    end tell
end run