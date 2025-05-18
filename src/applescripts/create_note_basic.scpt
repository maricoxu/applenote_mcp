-- create_note_basic.scpt
-- 接收参数: noteBody (纯文本内容), noteTitle (可选，笔记标题)
-- 功能: 在苹果备忘录的默认文件夹中创建一篇新笔记。

on run {noteBody_param, noteTitle_param}
    -- 确保参数存在，如果为空字符串则处理
    set noteBody to noteBody_param as string
    set noteTitle to noteTitle_param as string

    tell application "Notes"
        activate
        
        -- 默认在 Notes 文件夹（通常是 iCloud 下的 Notes 或"备忘录"账户下的"备忘录"文件夹）
        -- 对于更精确的控制，可能需要指定账户和文件夹，但基础版先用默认
        
        if noteTitle is not equal to ""
            make new note with properties {name:noteTitle, body:noteBody}
        else
            -- 如果没有提供标题，备忘录通常会使用内容的第一行作为标题，或者保持为空
            make new note with properties {body:noteBody}
        end if
    end tell
    
    return "Success: Note created."
end run