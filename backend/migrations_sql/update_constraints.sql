/*
 * Script de mise a jour des contraintes CHECK
 * Pour aligner la DB SQL Server avec les modeles Django
 *
 * A executer sur la base ArnaqueBD avant de lancer le backend.
 */

USE ArnaqueBD;
GO

-- ============================================================
-- 1. Ajouter le role 'autorite' a la table Utilisateur
-- ============================================================
IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_role')
BEGIN
    ALTER TABLE dbo.Utilisateur DROP CONSTRAINT CK_role;
    PRINT 'Ancienne contrainte CK_role supprimee.';
END
GO

ALTER TABLE dbo.Utilisateur
    ADD CONSTRAINT CK_role CHECK (role IN ('user', 'admin', 'autorite'));
PRINT 'Nouvelle contrainte CK_role ajoutee (user, admin, autorite).';
GO

-- ============================================================
-- 2. Ajouter les statuts manquants a la table Signalement
-- ============================================================
IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_statut')
BEGIN
    ALTER TABLE dbo.Signalement DROP CONSTRAINT CK_statut;
    PRINT 'Ancienne contrainte CK_statut supprimee.';
END
GO

ALTER TABLE dbo.Signalement
    ADD CONSTRAINT CK_statut CHECK (statut IN (
        'en_attente', 'approuve', 'rejete',
        'transmis', 'confirme', 'infirme'
    ));
PRINT 'Nouvelle contrainte CK_statut ajoutee (6 valeurs).';
GO

-- ============================================================
-- 3. Verification
-- ============================================================
SELECT
    tc.CONSTRAINT_NAME,
    tc.CHECK_CLAUSE
FROM sys.check_constraints cc
JOIN sys.check_constraints tc ON cc.object_id = tc.object_id
WHERE tc.name IN ('CK_role', 'CK_statut');
GO

PRINT 'Migration terminee avec succes.';
GO
