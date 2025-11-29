Create Table If Not Exists Users (
    ID Serial Not NULL Primary Key,
    User_Role varchar(10) Not NULL,
    User_Name varchar(20) Unique Not NULL,
    Email varchar(30) Unique Not NULL,
    User_Password varchar(15) Not NULL,

    Check(Email like '_%@_%._%'),
    Check(User_Role in ('Admin', 'Curator', 'EndUser'))
);

Create Table If Not Exists Document (
    ID Serial Not NULL Primary Key,
    Title varchar(80) Not NULL,
    Doc_Type varchar(20) Not NULL,
    Added_Time Timestamp Default now() Not NULL,
    Processed Boolean Default False Not NULL, 
    Added_By Int Not NULL,

    Foreign Key (Added_By) References Users(ID)
);

Create Table If Not Exists QueryLog (
    User_ID Int Not NULL,
    Query_Time Timestamp Default Now() Not NULL,
    Query_Text Text Not NULL,

    Foreign Key (User_ID) References Users(ID),
    Primary Key(User_ID, Query_Time)
);

Create Table If Not Exists Retrieved_Docs (
    User_ID Int Not NULL,
    Query_Time Timestamp Not NULL,
    Doc_ID Int Not NULL,
    
    Foreign Key (User_ID, Query_Time) References QueryLog(User_ID, Query_Time),
    Foreign Key (Doc_ID) References Document(ID),
    Primary Key(User_ID, Query_Time, Doc_ID)
);

Create Table If Not Exists Chunk_Embeddings (
    ID Serial Primary Key,
    Document_ID Int Not NULL,
    text Text NOT NULL,
    embedding_mini vector(384),
    embedding_qa vector(384),
    embedding_mpnet vector(768),

    Foreign Key (Document_ID) References Document(ID)
);