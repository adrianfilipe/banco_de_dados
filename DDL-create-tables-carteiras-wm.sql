

CREATE SCHEMA IF NOT EXISTS carteiras_wm;

SET search_path = carteiras_wm;

CREATE TABLE Fundo (
    IDFundo              INT          NOT NULL,
    NomeFundo            VARCHAR(100) NOT NULL,
    CNPJFundo            VARCHAR(20)  NOT NULL,
    SubclasseFundo       VARCHAR(10),
    ClassificacaoFundo   VARCHAR(10)  NOT NULL,
    PRIMARY KEY (IDFundo),
    UNIQUE (CNPJFundo)
);

CREATE TABLE Cliente (
    IDCliente        INT          NOT NULL,
    NomeCliente      VARCHAR(100) NOT NULL,
    CodigoCliente    VARCHAR(10)  NOT NULL,
    DocumentoCliente VARCHAR(20)  NOT NULL,
    PRIMARY KEY (IDCliente),
    UNIQUE (DocumentoCliente)
);

CREATE TABLE Ativo (
    IDAtivo    INT          NOT NULL,
    Setor      VARCHAR(50)  NOT NULL,
    Descricao  VARCHAR(200) NOT NULL,
    Tipo       VARCHAR(30)  NOT NULL,
    CNPJEmissor VARCHAR(20),
    DEN_SOC_EM  VARCHAR(100),
    ISIN        VARCHAR(20),
    PRIMARY KEY (IDAtivo),
    UNIQUE (CNPJEmissor)
);

CREATE TABLE Acao (
    IDAtivo           INT         NOT NULL,
    TickerAcao        VARCHAR(10) NOT NULL,
    ClassificacaoAcao VARCHAR(20),
    PRIMARY KEY (IDAtivo),
    UNIQUE (TickerAcao),
    FOREIGN KEY (IDAtivo) REFERENCES Ativo(IDAtivo)
);

CREATE TABLE Holding (
    IDHolding   INT         NOT NULL,
    CNPJHolding VARCHAR(20) NOT NULL,
    NomeHolding VARCHAR(100) NOT NULL,
    PRIMARY KEY (IDHolding),
    UNIQUE (CNPJHolding)
);

CREATE TABLE CotasFundo (
    IDAtivo INT NOT NULL,
    IDFundo INT NOT NULL,
    PRIMARY KEY (IDAtivo),
    FOREIGN KEY (IDAtivo) REFERENCES Ativo(IDAtivo),
    FOREIGN KEY (IDFundo) REFERENCES Fundo(IDFundo)
);

CREATE TABLE ParticipacaoHolding (
    IDAtivo   INT NOT NULL,
    IDHolding INT NOT NULL,
    PRIMARY KEY (IDAtivo),
    FOREIGN KEY (IDAtivo)   REFERENCES Ativo(IDAtivo),
    FOREIGN KEY (IDHolding) REFERENCES Holding(IDHolding)
);

CREATE TABLE Carteira_Cliente (
    DataCarteiraCliente DATE           NOT NULL,
    IDCliente           INT            NOT NULL,
    IDAtivo             INT            NOT NULL,
    VlrCartCliente      NUMERIC(15, 2) NOT NULL,
    Gestora             VARCHAR(50)    NOT NULL,
    QtdCartCliente      INT            NOT NULL,
    Plataforma          VARCHAR(20)    NOT NULL,
    PRIMARY KEY (DataCarteiraCliente, IDCliente, IDAtivo),
    FOREIGN KEY (IDCliente) REFERENCES Cliente(IDCliente),
    FOREIGN KEY (IDAtivo)   REFERENCES Ativo(IDAtivo)
);

CREATE TABLE Carteira_Fundo (
    DataCartFundo DATE           NOT NULL,
    IDAtivo       INT            NOT NULL,
    IDFundo       INT            NOT NULL,
    QtdCartFundo  INT            NOT NULL,
    VlrCartFundo  NUMERIC(15, 2) NOT NULL,
    PRIMARY KEY (DataCartFundo, IDAtivo, IDFundo),
    FOREIGN KEY (IDAtivo) REFERENCES Ativo(IDAtivo),
    FOREIGN KEY (IDFundo) REFERENCES Fundo(IDFundo)
);

CREATE TABLE Carteira_Holding (
    DataCartHolding DATE           NOT NULL,
    IDAtivo         INT            NOT NULL,
    IDHolding       INT            NOT NULL,
    VlrCartHolding  NUMERIC(15, 2) NOT NULL,
    QtdCartHolding  INT            NOT NULL,
    PRIMARY KEY (DataCartHolding, IDAtivo, IDHolding),
    FOREIGN KEY (IDAtivo)   REFERENCES Ativo(IDAtivo),
    FOREIGN KEY (IDHolding) REFERENCES Holding(IDHolding)
);

CREATE TABLE Compromisso_Cliente (
    DataCompromisso   DATE           NOT NULL,
    IDCliente         INT            NOT NULL,
    IDAtivo           INT            NOT NULL,
    ValorCompromissado NUMERIC(15, 2) NOT NULL,
    PRIMARY KEY (DataCompromisso, IDCliente, IDAtivo),
    FOREIGN KEY (IDCliente) REFERENCES Cliente(IDCliente),
    FOREIGN KEY (IDAtivo)   REFERENCES Ativo(IDAtivo)
);

CREATE TABLE TempDataFundo (
    DataBaseFundo   DATE           NOT NULL,
    TotalCotasFundo NUMERIC(20, 6) NOT NULL,
    IDFundo         INT            NOT NULL,
    PRIMARY KEY (DataBaseFundo, IDFundo),
    FOREIGN KEY (IDFundo) REFERENCES Fundo(IDFundo)
);

CREATE TABLE TempDataAtivo (
    DataBaseAtivo DATE           NOT NULL,
    IDAtivo       INT            NOT NULL,
    PrecoAtivo    NUMERIC(15, 4) NOT NULL,
    PRIMARY KEY (DataBaseAtivo, IDAtivo),
    FOREIGN KEY (IDAtivo) REFERENCES Ativo(IDAtivo)
);

CREATE TABLE TempDataHolding (
    DataHolding  DATE   NOT NULL,
    IDHolding    INT    NOT NULL,
    TotalAcoesHd BIGINT NOT NULL,
    PRIMARY KEY (DataHolding, IDHolding),
    FOREIGN KEY (IDHolding) REFERENCES Holding(IDHolding)
);
