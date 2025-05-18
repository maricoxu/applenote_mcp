-- list_notes.scpt
-- 接收参数: targetFolder_param (可选)
-- 功能: 列出指定文件夹中所有笔记的标题。如果未指定文件夹，则列出所有笔记的标题。
--       返回一个由换行符分隔的标题列表。

on run {targetFolder_param}
    set targetFolder to targetFolder_param as string
    set noteTitles to {} -- 用于存储标题的列表
    set outputString to ""

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

        if (count of searchScope) is equal to 0 then
            if targetFolder is not equal to "" then
                return "信息：文件夹 '" & targetFolder & "' 中没有笔记。"
            else
                return "信息：没有找到任何笔记。"
            end if
        end if

        repeat with aNote in searchScope
            set end of noteTitles to (name of aNote)
        end repeat

        -- 将标题列表转换为以换行符分隔的字符串
        set oldDelimiters to AppleScript's text item delimiters
        set AppleScript's text item delimiters to linefeed
        set outputString to noteTitles as string
        set AppleScript's text item delimiters to oldDelimiters -- 恢复原始分隔符

        return outputString
    end tell
end run