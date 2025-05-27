on run argv
    -- 参数：标题、内容、文件夹
    set noteTitle to item 1 of argv
    set noteContent to item 2 of argv
    set folderName to item 3 of argv
    
    tell application "Notes"
        activate
        
        -- 确定目标文件夹
        if folderName is not "" then
            try
                set targetFolder to folder folderName
            on error
                -- 如果文件夹不存在，创建它
                set targetFolder to make new folder with properties {name:folderName}
            end try
        else
            set targetFolder to default account's default folder
        end if
        
        -- 创建新笔记
        set newNote to make new note at targetFolder
        
        -- 设置标题
        if noteTitle is not "" then
            set name of newNote to noteTitle
        end if
        
        -- 创建富文本内容
        tell newNote
            -- 清空默认内容
            set body to ""
            
            -- 解析并添加内容（这里先用简单的方法）
            -- 后续我们会在Python中预处理内容
            set body to noteContent
        end tell
        
        return "Rich text note created successfully."
    end tell
end run 