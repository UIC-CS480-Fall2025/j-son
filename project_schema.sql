CREATE TABLE IF NOT EXISTS public.Users (
    ID SERIAL NOT NULL PRIMARY KEY,
    User_Role varchar(10) NOT NULL,
    User_Name varchar(20) Unique NOT NULL,
    Email varchar(30) Unique NOT NULL,
    User_Password varchar(15) NOT NULL,

    Check(Email like '_%@_%._%'),
    Check(User_Role in ('Admin', 'Curator', 'EndUser'))
);

CREATE TABLE IF NOT EXIST public.Document (
    ID SERIAL NOT NULL PRIMARY KEY,
    Title varchar(80) NOT NULL,
    Doc_Type varchar(20) NOT NULL,
    Added_Time Timestamp Default now() NOT NULL,
    Processed BOOLEAN DEFAULT False NOT NULL, 
    Added_By INT NOT NULL,

    Foreign Key (Added_By) References Users(ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXIST public.QueryLog (
    User_ID INT NOT NULL,
    Query_Time TIMESTAMP DEFAULT Now() NOT NULL,
    Query_Text TEXT NOT NULL,

    FOREGIN KEY (User_ID) REFERENCES Users(ID) ON DELETE CASCADE,
    PRIMARY KEY(User_ID, Query_Time)
);
CREATE TABLE IF NOT EXIST public.Retrieved_Docs (
    User_ID INT NOT NULL,
    Query_Time TIMESTAMP NOT NULL,
    Doc_ID INT NOT NULL,
    
    FOREIGN KEY (User_ID, Query_Time) REFERENCES QueryLog(User_ID, Query_Time),
    FOREIGN KEY (Doc_ID) REFERENCES Document(ID),
    PRIMARY KEY(User_ID, Query_Time, Doc_ID)
);

CREATE TABLE IF NOT EXIST public.Chunk_Embeddings (
    ID SERIAL PRIMARY KEY,
    Document_ID INT NOT NULL,
    Chunk_Text TEXT NOT NULL,
    Embedding_Mini vector(384),
    Embedding_QA vector(384),
    Embedding_MPNET vector(768),

    FOREIGN KEY (Document_ID) REFERENCES Document(ID) ON DELETE CASCADE
);