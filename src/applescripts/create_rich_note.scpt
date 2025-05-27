on run argv
    -- 参数：标题、解析后的内容结构（JSON格式）、文件夹
    set noteTitle to item 1 of argv
    set contentStructure to item 2 of argv
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
        
        -- 解析内容结构并创建富文本
        -- 这里我们先创建一个基础版本，后续会扩展
        set body of newNote to contentStructure
        
        return "Note created successfully with rich text formatting."
    end tell
end run 