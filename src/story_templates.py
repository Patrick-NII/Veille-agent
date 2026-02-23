from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StoryArchetype:
    name: str
    decision_label: str
    hooks: list[str]
    situations: list[str]
    decisions: list[str]
    workflow_before: list[str]
    workflow_after: list[str]
    outcomes: list[str]
    risks: list[str]
    strategic_questions: list[str]
    grid_strategy: str
    grid_architecture: str
    grid_governance: str
    grid_economics: str
    grid_risk: str
    signal_patterns: list[str]
    noise_patterns: list[str]
    action_patterns: list[str]
    budget_pattern: str
    risk_alert_pattern: str
    visual_types: list[str]


def archetypes() -> Mapping[str, StoryArchetype]:
    templates = [
        StoryArchetype(
            name="deploiement_copilot",
            decision_label="déploiement d'un copilote opérationnel",
            hooks=[
                "{company} n'a pas déployé un chatbot de plus: l'équipe a déplacé la décision au poste de travail.",
                "Le point clé n'est pas le modèle, c'est qui valide la décision produite par le copilote chez {company}.",
                "{company} a transformé un test IA dispersé en workflow piloté par des règles métiers.",
                "Ce cas montre comment {company} a réduit le temps d'analyse sans perdre le contrôle métier.",
                "Derrière le mot copilote, {company} a surtout redéfini la chaîne de décision.",
            ],
            situations=[
                "Chez {company}, les équipes {sector} perdaient du temps à reformuler les mêmes analyses entre opérations et data.",
                "La pression de délai a rendu visible un problème récurrent: les décisions locales arrivaient trop tard pour être utiles.",
                "Le volume de demandes internes a augmenté plus vite que la capacité des équipes à instruire chaque cas.",
            ],
            decisions=[
                "{company} a choisi un copilote ciblé sur un seul flux critique, avec validation humaine obligatoire.",
                "La direction a cadré un déploiement progressif, centré sur un workflow prioritaire plutôt qu'un lancement global.",
                "Le choix a été d'intégrer le copilote dans l'outil existant, sans multiplier les interfaces.",
            ],
            workflow_before=[
                "Demandes traitées par e-mail et feuilles partagées.",
                "Relectures successives entre équipes métier et data.",
                "Décision finale retardée par des allers-retours manuels.",
            ],
            workflow_after=[
                "Copilote propose une synthèse structurée dès la création du dossier.",
                "Validation métier en une étape avec règles explicites.",
                "Décision et justification archivées automatiquement pour audit.",
            ],
            outcomes=[
                "Le délai de traitement a baissé et la variabilité entre équipes a reculé.",
                "Le taux de dossiers traités au premier passage a progressé sur le flux cible.",
                "La visibilité managériale s'est améliorée grâce à des indicateurs quotidiens standardisés.",
            ],
            risks=[
                "La dépendance au prompt local crée des écarts de qualité entre équipes.",
                "Sans gouvernance des exceptions, le copilote peut déplacer les erreurs au lieu de les réduire.",
                "La performance perçue masque parfois un coût d'inférence mal suivi.",
            ],
            strategic_questions=[
                "Faut-il étendre le copilote à d'autres flux avant de stabiliser la gouvernance des exceptions?",
                "Quel niveau d'autonomie est acceptable sans diluer la responsabilité métier?",
                "Le gain observé justifie-t-il une industrialisation multi-sites dès ce trimestre?",
            ],
            grid_strategy="{company} lie le copilote à un objectif opérationnel mesurable.",
            grid_architecture="Intégration du copilote dans l'outil existant, sans nouvelle couche superflue.",
            grid_governance="Validation humaine obligatoire et règles d'exception documentées chez {company}.",
            grid_economics="Le ROI dépend du volume traité et du coût d'inférence unitaire.",
            grid_risk="Le risque majeur reste la dérive d'usage hors périmètre initial.",
            signal_patterns=[
                "Le signal fort: {company} transforme un usage IA en mécanisme de décision opérable.",
                "Le signal fort: la valeur vient du workflow révisé, pas d'une promesse algorithmique.",
            ],
            noise_patterns=[
                "Le bruit: confondre adoption de l'outil et amélioration réelle des décisions.",
            ],
            action_patterns=[
                "Limiter le périmètre à un flux et publier un KPI hebdomadaire de qualité décisionnelle.",
                "Formaliser les règles d'escalade avant toute extension multi-équipes.",
            ],
            budget_pattern="Allouer le budget par étape de déploiement validée sur KPI opérationnel.",
            risk_alert_pattern="Attention au risque de shadow prompts non audités dans les équipes terrain.",
            visual_types=["workflow_avant_apres", "boucle_feedback"],
        ),
        StoryArchetype(
            name="build_vs_buy_plateforme",
            decision_label="arbitrage build vs buy de la plateforme IA",
            hooks=[
                "Le vrai sujet chez {company}: acheter vite ou construire durablement.",
                "{company} a traité build vs buy comme une décision financière et non un débat technique.",
                "Ce cas montre comment un arbitrage plateforme change la vitesse d'exécution d'un programme IA.",
                "Chez {company}, la décision build vs buy a redéfini les responsabilités data et IT.",
                "Le point critique: {company} a mis un prix sur la flexibilité future.",
            ],
            situations=[
                "{company} gérait plusieurs preuves de concept sans socle commun ni coût consolidé.",
                "Les équipes perdaient en cohérence: chaque domaine utilisait un outil différent pour des besoins proches.",
                "La direction devait choisir entre accélération court terme et maîtrise long terme.",
            ],
            decisions=[
                "{company} a retenu une solution mixte: buy pour l'orchestration standard, build pour les briques différenciantes.",
                "Le choix final a fixé une frontière claire entre composants commodités et actifs stratégiques.",
                "La gouvernance d'architecture a imposé des critères de sortie avant signature fournisseur.",
            ],
            workflow_before=[
                "Chaîne hétérogène de POC par équipe.",
                "Coûts difficiles à consolider entre licences et infra.",
                "Décisions d'implémentation prises sans standard commun.",
            ],
            workflow_after=[
                "Catalogue unique des capacités plateforme.",
                "Comité d'architecture valide chaque nouveau cas d'usage.",
                "Suivi FinOps unifié avec seuils d'alerte mensuels.",
            ],
            outcomes=[
                "La vitesse de lancement des cas standards a augmenté.",
                "Le pilotage des coûts est devenu comparable entre domaines.",
                "La dette d'intégration a été réduite sur les flux critiques.",
            ],
            risks=[
                "Un contrat mal cadré peut figer la trajectoire d'architecture.",
                "Le mode hybride devient coûteux si les frontières build/buy restent floues.",
                "Le gain court terme peut masquer un lock-in progressif.",
            ],
            strategic_questions=[
                "Quels composants doivent rester internalisés pour protéger l'avantage métier?",
                "Le coût de sortie fournisseur est-il acceptable à horizon 24 mois?",
                "Le modèle d'exploitation cible est-il compatible avec les compétences disponibles?",
            ],
            grid_strategy="{company} transforme build vs buy en choix de portefeuille.",
            grid_architecture="Frontière build/buy explicite pour réduire la complexité d'intégration.",
            grid_governance="Critères d'entrée et de sortie fournisseur imposés par gouvernance.",
            grid_economics="Comparaison TCO sur 24 mois avant extension du périmètre.",
            grid_risk="Risque principal: lock-in progressif sous couvert de vitesse.",
            signal_patterns=[
                "Le signal fort: {company} structure la décision plateforme autour d'un modèle opératoire clair.",
                "Le signal fort: l'arbitrage économique est traité avant l'accélération commerciale.",
            ],
            noise_patterns=[
                "Le bruit: juger la plateforme uniquement sur le coût de licence initial.",
            ],
            action_patterns=[
                "Documenter la frontière build/buy par domaine métier dès le prochain comité.",
                "Mettre en place un indicateur trimestriel de coût de sortie fournisseur.",
            ],
            budget_pattern="Budgéter séparément les composants différenciants et les commodités.",
            risk_alert_pattern="Le lock-in contractuel peut neutraliser les gains de productivité annoncés.",
            visual_types=["roi_simple", "goulot_contrainte"],
        ),
        StoryArchetype(
            name="gouvernance_gating",
            decision_label="gouvernance par gates de décision",
            hooks=[
                "{company} n'a pas ajouté une couche de contrôle: l'entreprise a créé un mécanisme de passage obligé.",
                "Le changement clé chez {company}: plus de déploiement sans gate gouvernance explicite.",
                "Ce cas illustre comment un gate bien conçu accélère en évitant les retours arrière.",
                "Chez {company}, la gouvernance a cessé d'être un document pour devenir un flux.",
                "{company} a converti un risque diffus en points de décision vérifiables.",
            ],
            situations=[
                "{company} subissait des retards liés à des validations tardives sécurité, conformité et métiers.",
                "Les décisions de lancement étaient prises sans dossier de risque homogène.",
                "Le programme IA avançait vite, mais les incidents d'alignement augmentaient.",
            ],
            decisions=[
                "{company} a instauré trois gates obligatoires: données, modèle, exploitation.",
                "Chaque gate est adossé à un owner nommé et à des critères de passage explicites.",
                "La direction a conditionné le passage en production au respect complet des gates.",
            ],
            workflow_before=[
                "Validation gouvernance en fin de projet.",
                "Responsabilités partagées sans décisionnaire unique.",
                "Rework fréquent après revue conformité.",
            ],
            workflow_after=[
                "Gates intégrés dès la phase de cadrage.",
                "Décision de passage signée par owners identifiés.",
                "Journal de conformité réutilisable en audit.",
            ],
            outcomes=[
                "Le nombre de retours en arrière a diminué.",
                "La prévisibilité des délais de déploiement s'est améliorée.",
                "Les arbitrages COMEX reposent sur des critères stabilisés.",
            ],
            risks=[
                "Trop de gates peut recréer de la lourdeur si la granularité est mal calibrée.",
                "Sans automatisation, la gouvernance peut devenir un goulot administratif.",
                "Le risque de contournement existe si les objectifs ne sont pas alignés.",
            ],
            strategic_questions=[
                "Quel niveau de contrôle conserve la vitesse sans affaiblir la responsabilité?",
                "Les gates actuels couvrent-ils vraiment les risques opérationnels majeurs?",
                "Comment mesurer l'efficacité des gates au-delà du simple respect process?",
            ],
            grid_strategy="{company} aligne vitesse et contrôle via des gates décisionnels.",
            grid_architecture="Les gates sont branchés sur les étapes réelles du workflow.",
            grid_governance="Owners nommés et critères de passage objectivés.",
            grid_economics="Moins de rework réduit le coût caché de gouvernance.",
            grid_risk="Risque de contournement si les incitations restent contradictoires.",
            signal_patterns=[
                "Le signal fort: la gouvernance devient un mécanisme d'exécution, pas une checklist.",
                "Le signal fort: {company} rend chaque passage traçable et attribuable.",
            ],
            noise_patterns=[
                "Le bruit: croire qu'ajouter des validations suffit sans ownership clair.",
            ],
            action_patterns=[
                "Définir trois gates maximum et un owner unique par gate.",
                "Automatiser la collecte des preuves pour éviter la surcharge manuelle.",
            ],
            budget_pattern="Financer l'automatisation des gates avant d'étendre le périmètre IA.",
            risk_alert_pattern="Une gouvernance purement documentaire augmente le risque de dette process.",
            visual_types=["goulot_contrainte", "boucle_feedback"],
        ),
        StoryArchetype(
            name="industrialisation_mlops",
            decision_label="industrialisation MLOps",
            hooks=[
                "{company} a cessé d'empiler des modèles: l'équipe a industrialisé la chaîne de livraison.",
                "Le gain chez {company} vient moins des algorithmes que de la discipline MLOps.",
                "Ce cas montre comment un pipeline fiable transforme la valeur business.",
                "Chez {company}, la question est passée de 'quel modèle?' à 'quel niveau de service?'.",
                "{company} a réduit l'improvisation en production par une chaîne MLOps standardisée.",
            ],
            situations=[
                "{company} livrait des modèles performants en test mais instables en exploitation.",
                "Les incidents post-déploiement consommaient le temps des équipes data et plateforme.",
                "Le rythme de mise en production restait trop lent pour les besoins métiers.",
            ],
            decisions=[
                "{company} a standardisé un pipeline MLOps avec tests, monitoring et rollback.",
                "Les mises en production sont passées sous contrôle de SLO explicites.",
                "Le programme a imposé un socle d'observabilité commun à tous les cas d'usage.",
            ],
            workflow_before=[
                "Déploiements ad hoc selon les équipes.",
                "Surveillance manuelle des performances en production.",
                "Correction réactive après incidents.",
            ],
            workflow_after=[
                "Pipeline CI/CD modèle standard pour tous les flux.",
                "Monitoring drift et performance avec alertes automatiques.",
                "Rollback guidé par runbook partagé.",
            ],
            outcomes=[
                "La fiabilité de production a progressé et les interruptions ont baissé.",
                "Le délai entre expérimentation et mise en production a diminué.",
                "La charge d'urgence des équipes a reculé.",
            ],
            risks=[
                "L'outillage peut devenir fragmenté si chaque domaine personnalise trop tôt.",
                "Sans gouvernance des features, la dette technique revient rapidement.",
                "Le coût d'observabilité peut dériver sans priorisation des métriques.",
            ],
            strategic_questions=[
                "Quel niveau de standardisation MLOps est nécessaire par domaine?",
                "Quand faut-il accepter une exception au pipeline standard?",
                "Quel indicateur doit piloter la priorité de fiabilisation?",
            ],
            grid_strategy="{company} relie MLOps à un niveau de service métier.",
            grid_architecture="Pipeline unique pour limiter les bifurcations techniques.",
            grid_governance="Runbooks et ownership d'incident standardisés chez {company}.",
            grid_economics="Moins d'incidents réduit le coût d'exploitation non planifié.",
            grid_risk="Risque principal: dette cachée dans les exceptions pipeline.",
            signal_patterns=[
                "Le signal fort: {company} industrialise la livraison avant d'élargir le portefeuille.",
                "Le signal fort: la stabilité devient un KPI stratégique, pas seulement technique.",
            ],
            noise_patterns=[
                "Le bruit: focaliser la discussion sur un benchmark modèle isolé.",
            ],
            action_patterns=[
                "Fixer un SLO commun et un runbook obligatoire par cas d'usage.",
                "Prioriser la dette MLOps des flux à plus fort impact opérationnel.",
            ],
            budget_pattern="Allouer le budget MLOps selon le coût historique des incidents.",
            risk_alert_pattern="Sans discipline d'exception, la plateforme MLOps se fragmente vite.",
            visual_types=["workflow_avant_apres", "boucle_feedback"],
        ),
        StoryArchetype(
            name="contrainte_finops",
            decision_label="pilotage FinOps de l'IA en production",
            hooks=[
                "Le cas {company}: la contrainte n'était pas la donnée, mais la facture d'exploitation.",
                "{company} a découvert que le coût unitaire IA décidait du rythme d'adoption.",
                "Ce cas rappelle qu'un programme IA sans FinOps explicite perd sa trajectoire.",
                "Chez {company}, l'enjeu était de protéger la marge tout en gardant la vitesse.",
                "{company} a transformé une alerte coûts en décision de portefeuille.",
            ],
            situations=[
                "Les charges d'inférence de {company} augmentaient plus vite que la valeur captée.",
                "La visibilité des coûts par cas d'usage était insuffisante pour arbitrer.",
                "Le pilotage budgétaire suivait les dépenses globales sans granularité opérationnelle.",
            ],
            decisions=[
                "{company} a instauré des seuils FinOps par flux et un suivi du coût unitaire.",
                "Les équipes ont relié chaque déploiement à une hypothèse de valeur chiffrée.",
                "Le financement a été conditionné au respect des garde-fous de coût.",
            ],
            workflow_before=[
                "Suivi mensuel global des dépenses IA.",
                "Aucune comparaison coût/valeur par cas d'usage.",
                "Décisions de scale prises sans seuil financier.",
            ],
            workflow_after=[
                "Tableau FinOps par flux avec coût unitaire.",
                "Revue hebdomadaire coût/valeur avec owners métiers.",
                "Extension conditionnée à un ratio économique explicite.",
            ],
            outcomes=[
                "La trajectoire de coût a été stabilisée.",
                "Les cas non performants ont été stoppés plus tôt.",
                "La discussion budget est devenue factuelle et comparable.",
            ],
            risks=[
                "Une réduction de coût trop agressive peut dégrader la qualité de service.",
                "Les équipes peuvent optimiser la métrique coût au détriment de la valeur réelle.",
                "Le risque d'under-provisioning augmente si les seuils sont mal calibrés.",
            ],
            strategic_questions=[
                "Quel seuil de coût unitaire est acceptable par domaine métier?",
                "Quel cas d'usage doit être arrêté malgré une adoption interne élevée?",
                "Comment préserver la qualité tout en maîtrisant l'inférence?",
            ],
            grid_strategy="{company} pilote l'IA comme un portefeuille sous contrainte de marge.",
            grid_architecture="Choix d'architecture guidés par coût unitaire en production.",
            grid_governance="Revue hebdomadaire coût/valeur avec owners nommés.",
            grid_economics="Extension des usages conditionnée au seuil économique défini.",
            grid_risk="Risque: couper trop vite et dégrader l'expérience métier.",
            signal_patterns=[
                "Le signal fort: {company} convertit le FinOps en mécanisme de décision.",
                "Le signal fort: le coût unitaire devient un indicateur de pilotage stratégique.",
            ],
            noise_patterns=[
                "Le bruit: suivre seulement la facture globale sans granularité par flux.",
            ],
            action_patterns=[
                "Calculer un coût unitaire par cas d'usage dès ce cycle budgétaire.",
                "Stopper les usages sans trajectoire valeur/coût défendable.",
            ],
            budget_pattern="Rebaser le budget IA sur des seuils coût/valeur par flux.",
            risk_alert_pattern="Un FinOps purement comptable peut casser l'adoption métier.",
            visual_types=["roi_simple", "goulot_contrainte"],
        ),
        StoryArchetype(
            name="socle_data_industriel",
            decision_label="construction d'un socle data industriel",
            hooks=[
                "{company} n'a pas gagné avec un nouveau modèle: l'entreprise a stabilisé le socle data.",
                "Le point de rupture chez {company} était la qualité des flux, pas l'algorithme.",
                "Ce cas montre que la valeur IA dépend d'abord de la chaîne de données.",
                "Chez {company}, la priorité est devenue l'alignement des référentiels.",
                "{company} a traité la dette data comme un sujet stratégique, pas technique.",
            ],
            situations=[
                "Les flux de données de {company} présentaient des versions contradictoires selon les systèmes.",
                "Les équipes perdaient du temps à réconcilier des référentiels non alignés.",
                "Les cas IA butaient sur des ruptures de qualité en amont.",
            ],
            decisions=[
                "{company} a lancé un socle data commun avec règles de qualité et ownership explicite.",
                "Le programme a défini des contrats de données entre domaines producteurs et consommateurs.",
                "Les priorités IA ont été réalignées sur les flux disposant d'un socle fiable.",
            ],
            workflow_before=[
                "Données collectées par silos métier.",
                "Corrections manuelles récurrentes avant chaque analyse.",
                "Décisions retardées par incertitude sur la donnée.",
            ],
            workflow_after=[
                "Contrats de données versionnés par domaine.",
                "Contrôles qualité automatiques avant exposition.",
                "Décision alimentée par un référentiel consolidé.",
            ],
            outcomes=[
                "La confiance dans les indicateurs a progressé.",
                "Le temps de préparation des analyses a diminué.",
                "Les projets IA ont gagné en régularité d'exécution.",
            ],
            risks=[
                "Le socle peut devenir centralisateur et lent sans gouvernance distribuée.",
                "Les domaines peuvent contourner les standards sous pression opérationnelle.",
                "Le backlog qualité peut dériver si les responsabilités sont floues.",
            ],
            strategic_questions=[
                "Quel niveau de standard data est requis avant d'étendre les usages IA?",
                "Comment équilibrer standard global et autonomie locale des domaines?",
                "Quelle dette data doit être traitée en priorité pour soutenir la roadmap?",
            ],
            grid_strategy="{company} fait du socle data un actif de portefeuille IA.",
            grid_architecture="Contrats de données imposent une intégration plus stable.",
            grid_governance="Ownership qualité explicite entre producteurs et consommateurs.",
            grid_economics="Moins de retraitement manuel améliore la productivité analytique.",
            grid_risk="Risque majeur: contournement local des standards communs.",
            signal_patterns=[
                "Le signal fort: {company} sécurise la valeur IA en amont des modèles.",
                "Le signal fort: la discipline data réduit les arbitrages défensifs en comité.",
            ],
            noise_patterns=[
                "Le bruit: promettre des gains IA sans trajectoire de qualité data.",
            ],
            action_patterns=[
                "Nommer un owner qualité par flux critique.",
                "Prioriser trois contrats de données à fort impact business.",
            ],
            budget_pattern="Budgéter le socle data selon le coût évité de retraitement.",
            risk_alert_pattern="Sans ownership data, la dette revient plus vite que la valeur livrée.",
            visual_types=["workflow_avant_apres", "goulot_contrainte"],
        ),
        StoryArchetype(
            name="gouvernance_securite",
            decision_label="gouvernance sécurité des usages IA",
            hooks=[
                "{company} a découvert que la vitesse IA sans sécurité explicite détruit la confiance.",
                "Le cas {company} montre comment sécurité et delivery peuvent converger.",
                "Ce n'est pas une histoire d'interdiction: {company} a redessiné les règles d'accès.",
                "Chez {company}, la gouvernance sécurité est devenue un levier d'adoption.",
                "{company} a transformé un risque diffus en politique opérationnelle.",
            ],
            situations=[
                "Des usages IA de {company} exposaient des données sensibles sans contrôle homogène.",
                "Les équipes avançaient plus vite que les règles de sécurité applicables.",
                "Le COMEX demandait une trajectoire claire entre innovation et conformité.",
            ],
            decisions=[
                "{company} a instauré une gouvernance sécurité par niveau de sensibilité des données.",
                "Les accès ont été segmentés et les sorties de données tracées.",
                "Chaque nouveau cas IA est évalué via une revue sécurité standardisée.",
            ],
            workflow_before=[
                "Accès données accordés au cas par cas.",
                "Traçabilité partielle des interactions IA.",
                "Validation sécurité tardive avant mise en production.",
            ],
            workflow_after=[
                "Classification des données intégrée au workflow.",
                "Journalisation systématique des usages sensibles.",
                "Revue sécurité en amont du déploiement.",
            ],
            outcomes=[
                "Le niveau de conformité perçu s'est renforcé.",
                "Les incidents potentiels sont détectés plus tôt.",
                "La coordination sécurité/data est devenue plus fluide.",
            ],
            risks=[
                "Un excès de contrôle peut bloquer les cas à faible risque.",
                "La politique peut dériver si les exceptions ne sont pas gouvernées.",
                "La confiance peut se dégrader en cas d'incident mal communiqué.",
            ],
            strategic_questions=[
                "Quel équilibre entre contrôle et vitesse est acceptable par domaine?",
                "Quelles exceptions sécurité doivent être autorisées et dans quelles limites?",
                "Comment démontrer la robustesse du dispositif au niveau COMEX?",
            ],
            grid_strategy="{company} relie sécurité IA et confiance de gouvernance.",
            grid_architecture="Traçabilité intégrée dans les composants d'accès et d'usage.",
            grid_governance="Revue sécurité standard avant passage en production.",
            grid_economics="Les coûts de contrôle évitent des incidents à fort impact.",
            grid_risk="Risque: politique d'exception non maîtrisée dans le temps.",
            signal_patterns=[
                "Le signal fort: {company} transforme la sécurité en cadence de décision.",
                "Le signal fort: la conformité est rendue opérable, pas seulement déclarative.",
            ],
            noise_patterns=[
                "Le bruit: opposer systématiquement sécurité et innovation.",
            ],
            action_patterns=[
                "Classifier les flux sensibles et standardiser les revues d'accès.",
                "Mettre en place un registre d'exceptions avec date de revue.",
            ],
            budget_pattern="Protéger un budget dédié au contrôle des flux sensibles.",
            risk_alert_pattern="Le principal risque est l'accumulation d'exceptions non revues.",
            visual_types=["boucle_feedback", "goulot_contrainte"],
        ),
        StoryArchetype(
            name="modernisation_architecture",
            decision_label="modernisation d'architecture orientée IA",
            hooks=[
                "Chez {company}, l'IA a forcé une décision d'architecture que l'entreprise repoussait.",
                "Le cas {company}: moderniser l'architecture pour éviter d'empiler des contournements.",
                "Ce mouvement n'est pas cosmétique: {company} redéfinit son socle d'intégration.",
                "La vraie décision de {company} porte sur la dette future, pas sur le prochain use case.",
                "{company} transforme une contrainte technique en trajectoire stratégique.",
            ],
            situations=[
                "L'architecture historique de {company} freinait la mise à l'échelle des cas IA.",
                "Les intégrations ponctuelles créaient une dette croissante entre systèmes.",
                "La roadmap IA exposait des limites de performance et de maintenabilité.",
            ],
            decisions=[
                "{company} a engagé une modernisation progressive avec interfaces standardisées.",
                "Le programme a priorisé les composants à forte dette avant d'élargir le portefeuille.",
                "Les choix techniques ont été pilotés par des critères d'exploitabilité.",
            ],
            workflow_before=[
                "Intégrations point à point par projet.",
                "Dépendances fortes entre applications legacy.",
                "Délai long pour chaque nouveau cas d'usage IA.",
            ],
            workflow_after=[
                "Interfaces normalisées entre domaines.",
                "Composants découplés pour accélérer les évolutions.",
                "Déploiement IA appuyé sur un socle réutilisable.",
            ],
            outcomes=[
                "La vitesse d'intégration des nouveaux cas a progressé.",
                "La dette technique explicite a été réduite sur le périmètre prioritaire.",
                "La coordination entre équipes plateforme et métier est plus prévisible.",
            ],
            risks=[
                "Le chantier peut dériver si la séquence de migration est mal priorisée.",
                "Le coût de transition peut dépasser la valeur court terme attendue.",
                "Des architectures hybrides prolongées peuvent créer une complexité durable.",
            ],
            strategic_questions=[
                "Quelle part de legacy doit être conservée à horizon 24 mois?",
                "Quel niveau de refonte est nécessaire pour soutenir la roadmap IA?",
                "Comment arbitrer entre vitesse projet et cohérence d'architecture?",
            ],
            grid_strategy="{company} modernise pour sécuriser la trajectoire IA pluriannuelle.",
            grid_architecture="Interfaces standardisées réduisent la dette d'intégration future.",
            grid_governance="Priorisation des migrations pilotée par comité d'architecture.",
            grid_economics="Le coût de transition est comparé à la dette évitée.",
            grid_risk="Risque majeur: hybridation trop longue et coûteuse.",
            signal_patterns=[
                "Le signal fort: {company} traite l'architecture comme levier de valeur.",
                "Le signal fort: la dette technique devient un paramètre de décision budgétaire.",
            ],
            noise_patterns=[
                "Le bruit: reporter la dette d'architecture au prochain cycle.",
            ],
            action_patterns=[
                "Prioriser trois migrations qui débloquent le plus de valeur IA.",
                "Mesurer la dette évitée au même niveau que le coût de transformation.",
            ],
            budget_pattern="Étaler le budget de modernisation selon des jalons d'exploitabilité.",
            risk_alert_pattern="Une modernisation sans séquence ferme peut créer une double dette.",
            visual_types=["workflow_avant_apres", "roi_simple"],
        ),
    ]
    return {template.name: template for template in templates}
