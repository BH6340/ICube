USE `icube_db`;
-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: icube_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `email` varchar(254) NOT NULL,
  `username` varchar(60) NOT NULL,
  `bio` longtext NOT NULL,
  `image` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `accounts_user_username_6088629e_uniq` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user`
--

LOCK TABLES `accounts_user` WRITE;
/*!40000 ALTER TABLE `accounts_user` DISABLE KEYS */;
INSERT INTO `accounts_user` VALUES (1,'pbkdf2_sha256$1200000$wwSqWroPaylmBPEEypn13v$wsXa3FcTXGAixXKlWvBK41XawV/8PlRan8Ikg/M8UgE=',NULL,0,0,1,'2026-05-11 13:04:43.160321','bh01@qq.com','bh01','这是bh01的测试简介','/media/avatars/admin_TvFlaQx.png'),(2,'pbkdf2_sha256$1200000$r3OXdjnkCUkkD8dsYwKvYI$tVLlEmIIgIzLbEuuQK2DNcQADpHDx2dNLaFx0jBC978=',NULL,0,0,1,'2026-05-11 14:58:32.159835','bh02@qq.com','bh02','这是bh02的简介','avatars/avatar_2_d43037d8_kARyCpc.svg'),(3,'pbkdf2_sha256$1200000$cJ7IS2DNMwk53YoArSUDWB$09KSEoIzAND7FptTUGF69r9Wfvn58LXDiUOYaa8Uq3U=',NULL,0,0,1,'2026-05-11 14:58:56.644541','bh03@qq.com','bh03','这是bh03的简介','avatars/avatar_3_599f7828_JWU26XE.svg'),(4,'pbkdf2_sha256$1200000$1U3JbJi7IJmftkdvH2cafI$KnEY+mhMfb+DHo9EadnmWPWuVq28sDswnhG/Ixxit8s=',NULL,0,0,1,'2026-05-11 14:59:20.745717','bh04@qq.com','bh04','这是bh04的简介','avatars/avatar_4_07eddaaf_WeeKHJx.svg'),(5,'pbkdf2_sha256$1200000$WRHGASrWYmCTFXQaZUwadz$N5eocKcaXp0pYcZnT07NhKqhsvi6OFje6EPCUWnO7uk=',NULL,0,0,1,'2026-05-11 19:11:36.539452','bh05@qq.com','bh05','魔方爱好者','avatars/avatar_5_42c5b22d_JMH7ua4.svg'),(6,'pbkdf2_sha256$1200000$okkHb5GNQKwfvBOnAQJ5de$oTBOGz7ODepDV/+iQKHXc8wnGcmzwO0FtbbmGwdt4I8=','2026-07-24 14:13:00.721822',1,1,1,'2026-05-12 08:26:47.622264','baihao6340@163.com','','','avatars/avatar_6_65294af4_B6xyUSz.svg'),(7,'pbkdf2_sha256$1200000$RYFGlCvA1CDRxSNdklva6T$kXTRELt9ADjwvXRzQ7vBw4qlYiKkYsHbLDMtsdqHy7c=',NULL,0,0,1,'2026-05-12 10:31:45.718088','bh06@qq.com','bh06','','avatars/avatar_7_4a4a872f_GADdPGB.svg'),(8,'pbkdf2_sha256$1200000$DnUCKmEqnGwe6dgpusKgbv$dWypTxpzl3XsLQTHMtP2kVzzgSlZGrPXhDQvoFrI04I=',NULL,0,0,1,'2026-06-03 10:52:12.092033','bh06@163.com','bh06_1','','avatars/avatar_8_539a8195_i4KcIT3.svg'),(9,'pbkdf2_sha256$1200000$ftzQsmKyRLAeMfinPTKybA$HhvTRYfZhcto+EM0AkQcrw40kW595wOvrUz9i6d0/dY=',NULL,0,0,1,'2026-06-03 14:36:26.343585','bh07@qq.com','bh07','','avatars/avatar_9_f143219d_ZijIf6X.svg'),(10,'pbkdf2_sha256$1200000$jp60Dr1nt6eO4OfAqfD5Qv$yGPq7Od8NvPd5UZXv/PytTyviaCqWLBGPZFgB5vR06E=',NULL,0,0,1,'2026-06-03 14:54:47.046829','bh08@qq.com','bh08','新的个人介绍0817','avatars/upload_avatar_hmPz9pO.webp'),(11,'pbkdf2_sha256$1200000$HnHuO67UPNA3KGzqrdciHY$BEGRtyOatdrHIGDWKfQyC8zc2gE9HkTmxTtSBUUMtAM=',NULL,0,0,1,'2026-06-05 09:55:05.648601','user1@example.com','魔方小白','魔方爱好者，欢迎交流！','avatars/avatar_11_50d05158_tAG2QVH.svg'),(12,'pbkdf2_sha256$1200000$K4RZs6x8mUSPOBiwKYSfpG$m1sUeywn5sSlmRjpG9NYv9v/CLItOlun+BLJpCPab9M=',NULL,0,0,1,'2026-06-05 09:55:07.421317','user2@example.com','速拧大神','魔方爱好者，欢迎交流！','avatars/avatar_12_23b2b646_RidBlom.svg'),(13,'pbkdf2_sha256$1200000$NUI8BH6NjcYEnrSe8l5O4V$PR0PnTdasbMdgc3gewGRKWuk6CRdEaEkyoXrzhpLxSc=',NULL,0,0,1,'2026-06-05 09:55:09.104099','user3@example.com','公式收藏家','魔方爱好者，欢迎交流！','avatars/avatar_13_61701999_4yQ9tw8.svg'),(15,'pbkdf2_sha256$1200000$AWyslHhILW6eJAhu7XQPXC$HrQbn7QsET2D7UZvcwIY3sipNk/CDeMV8lIzNnAR1+M=',NULL,0,0,1,'2026-07-24 17:37:27.677024','test@test.com','testuser','',''),(16,'pbkdf2_sha256$1200000$Tiy7ilP3yPpw9fw0GJk0AQ$g1fcszaIBUFeZeSNCv4txXz/b20cpN1oaiOG3f/uOvE=',NULL,0,0,1,'2026-07-25 11:19:24.352279','testapi@test.com','testapi','',''),(17,'pbkdf2_sha256$1200000$4eYotvsLOUT6KceXwGcLVX$HsB7VEl/kcMbvGhgJxxZE6vBlDWq0XecdYHgW576jog=',NULL,0,0,1,'2026-08-17 10:54:44.388962','bh007@qq.com','bh007','','avatars/upload_avatar.webp');
/*!40000 ALTER TABLE `accounts_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_followers`
--

DROP TABLE IF EXISTS `accounts_user_followers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_followers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `from_user_id` bigint NOT NULL,
  `to_user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_followers_from_user_id_to_user_id_ad929616_uniq` (`from_user_id`,`to_user_id`),
  KEY `accounts_user_followers_to_user_id_6dddd47f_fk_accounts_user_id` (`to_user_id`),
  CONSTRAINT `accounts_user_follow_from_user_id_1e8ec42b_fk_accounts_` FOREIGN KEY (`from_user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `accounts_user_followers_to_user_id_6dddd47f_fk_accounts_user_id` FOREIGN KEY (`to_user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_followers`
--

LOCK TABLES `accounts_user_followers` WRITE;
/*!40000 ALTER TABLE `accounts_user_followers` DISABLE KEYS */;
INSERT INTO `accounts_user_followers` VALUES (3,2,1),(10,2,10),(2,3,1),(11,3,10),(8,5,1);
/*!40000 ALTER TABLE `accounts_user_followers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_groups`
--

LOCK TABLES `accounts_user_groups` WRITE;
/*!40000 ALTER TABLE `accounts_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_user_permissions`
--

LOCK TABLES `accounts_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=121 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add 用户',6,'add_user'),(22,'Can change 用户',6,'change_user'),(23,'Can delete 用户',6,'delete_user'),(24,'Can view 用户',6,'view_user'),(25,'Can add 标签',13,'add_tag'),(26,'Can change 标签',13,'change_tag'),(27,'Can delete 标签',13,'delete_tag'),(28,'Can view 标签',13,'view_tag'),(29,'Can add 帖子',9,'add_post'),(30,'Can change 帖子',9,'change_post'),(31,'Can delete 帖子',9,'delete_post'),(32,'Can view 帖子',9,'view_post'),(33,'Can add 评论',7,'add_comment'),(34,'Can change 评论',7,'change_comment'),(35,'Can delete 评论',7,'delete_comment'),(36,'Can view 评论',7,'view_comment'),(37,'Can add comment like',8,'add_commentlike'),(38,'Can change comment like',8,'change_commentlike'),(39,'Can delete comment like',8,'delete_commentlike'),(40,'Can view comment like',8,'view_commentlike'),(41,'Can add post collect',10,'add_postcollect'),(42,'Can change post collect',10,'change_postcollect'),(43,'Can delete post collect',10,'delete_postcollect'),(44,'Can view post collect',10,'view_postcollect'),(45,'Can add post like',11,'add_postlike'),(46,'Can change post like',11,'change_postlike'),(47,'Can delete post like',11,'delete_postlike'),(48,'Can view post like',11,'view_postlike'),(49,'Can add 举报',12,'add_report'),(50,'Can change 举报',12,'change_report'),(51,'Can delete 举报',12,'delete_report'),(52,'Can view 举报',12,'view_report'),(53,'Can add 帖子标签',14,'add_posttag'),(54,'Can change 帖子标签',14,'change_posttag'),(55,'Can delete 帖子标签',14,'delete_posttag'),(56,'Can view 帖子标签',14,'view_posttag'),(57,'Can add 导航菜单',15,'add_navigationmenu'),(58,'Can change 导航菜单',15,'change_navigationmenu'),(59,'Can delete 导航菜单',15,'delete_navigationmenu'),(60,'Can view 导航菜单',15,'view_navigationmenu'),(61,'Can add formula collection',19,'add_formulacollection'),(62,'Can change formula collection',19,'change_formulacollection'),(63,'Can delete formula collection',19,'delete_formulacollection'),(64,'Can view formula collection',19,'view_formulacollection'),(65,'Can add cube category',16,'add_cubecategory'),(66,'Can change cube category',16,'change_cubecategory'),(67,'Can delete cube category',16,'delete_cubecategory'),(68,'Can view cube category',16,'view_cubecategory'),(69,'Can add formula tag',20,'add_formulatag'),(70,'Can change formula tag',20,'change_formulatag'),(71,'Can delete formula tag',20,'delete_formulatag'),(72,'Can view formula tag',20,'view_formulatag'),(73,'Can add formula tag relation',21,'add_formulatagrelation'),(74,'Can change formula tag relation',21,'change_formulatagrelation'),(75,'Can delete formula tag relation',21,'delete_formulatagrelation'),(76,'Can view formula tag relation',21,'view_formulatagrelation'),(77,'Can add formula',18,'add_formula'),(78,'Can change formula',18,'change_formula'),(79,'Can delete formula',18,'delete_formula'),(80,'Can view formula',18,'view_formula'),(81,'Can add cube state',17,'add_cubestate'),(82,'Can change cube state',17,'change_cubestate'),(83,'Can delete cube state',17,'delete_cubestate'),(84,'Can view cube state',17,'view_cubestate'),(85,'Can add product',25,'add_product'),(86,'Can change product',25,'change_product'),(87,'Can delete product',25,'delete_product'),(88,'Can view product',25,'view_product'),(89,'Can add order item',24,'add_orderitem'),(90,'Can change order item',24,'change_orderitem'),(91,'Can delete order item',24,'delete_orderitem'),(92,'Can view order item',24,'view_orderitem'),(93,'Can add order',23,'add_order'),(94,'Can change order',23,'change_order'),(95,'Can delete order',23,'delete_order'),(96,'Can view order',23,'view_order'),(97,'Can add cart',22,'add_cart'),(98,'Can change cart',22,'change_cart'),(99,'Can delete cart',22,'delete_cart'),(100,'Can view cart',22,'view_cart'),(101,'Can add product category',26,'add_productcategory'),(102,'Can change product category',26,'change_productcategory'),(103,'Can delete product category',26,'delete_productcategory'),(104,'Can view product category',26,'view_productcategory'),(105,'Can add 帖子图片',27,'add_postimage'),(106,'Can change 帖子图片',27,'change_postimage'),(107,'Can delete 帖子图片',27,'delete_postimage'),(108,'Can view 帖子图片',27,'view_postimage'),(109,'Can add timer record',28,'add_timerrecord'),(110,'Can change timer record',28,'change_timerrecord'),(111,'Can delete timer record',28,'delete_timerrecord'),(112,'Can view timer record',28,'view_timerrecord'),(113,'Can add 轮播图',29,'add_banner'),(114,'Can change 轮播图',29,'change_banner'),(115,'Can delete 轮播图',29,'delete_banner'),(116,'Can view 轮播图',29,'view_banner'),(117,'Can add 收货地址',30,'add_address'),(118,'Can change 收货地址',30,'change_address'),(119,'Can delete 收货地址',30,'delete_address'),(120,'Can view 收货地址',30,'view_address');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-07-24 14:16:06.395001','4','CFOP复原步骤',1,'[{\"added\": {}}]',29,6),(2,'2026-07-24 14:27:41.737832','4','CFOP复原步骤',3,'',29,6);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (6,'accounts','user'),(1,'admin','logentry'),(2,'auth','group'),(3,'auth','permission'),(4,'contenttypes','contenttype'),(16,'formula','cubecategory'),(17,'formula','cubestate'),(18,'formula','formula'),(19,'formula','formulacollection'),(20,'formula','formulatag'),(21,'formula','formulatagrelation'),(7,'forum','comment'),(8,'forum','commentlike'),(9,'forum','post'),(10,'forum','postcollect'),(27,'forum','postimage'),(11,'forum','postlike'),(14,'forum','posttag'),(12,'forum','report'),(13,'forum','tag'),(29,'home','banner'),(15,'home','navigationmenu'),(5,'sessions','session'),(30,'shop','address'),(22,'shop','cart'),(23,'shop','order'),(24,'shop','orderitem'),(25,'shop','product'),(26,'shop','productcategory'),(28,'timer','timerrecord');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-05-11 11:09:50.047858'),(2,'contenttypes','0002_remove_content_type_name','2026-05-11 11:09:50.165399'),(3,'auth','0001_initial','2026-05-11 11:09:50.642447'),(4,'auth','0002_alter_permission_name_max_length','2026-05-11 11:09:50.731748'),(5,'auth','0003_alter_user_email_max_length','2026-05-11 11:09:50.740862'),(6,'auth','0004_alter_user_username_opts','2026-05-11 11:09:50.751689'),(7,'auth','0005_alter_user_last_login_null','2026-05-11 11:09:50.759935'),(8,'auth','0006_require_contenttypes_0002','2026-05-11 11:09:50.764363'),(9,'auth','0007_alter_validators_add_error_messages','2026-05-11 11:09:50.773620'),(10,'auth','0008_alter_user_username_max_length','2026-05-11 11:09:50.783168'),(11,'auth','0009_alter_user_last_name_max_length','2026-05-11 11:09:50.792065'),(12,'auth','0010_alter_group_name_max_length','2026-05-11 11:09:50.816275'),(13,'auth','0011_update_proxy_permissions','2026-05-11 11:09:50.826561'),(14,'auth','0012_alter_user_first_name_max_length','2026-05-11 11:09:50.836370'),(15,'accounts','0001_initial','2026-05-11 11:09:51.547459'),(16,'admin','0001_initial','2026-05-11 11:09:51.773729'),(17,'admin','0002_logentry_remove_auto_add','2026-05-11 11:09:51.786071'),(18,'admin','0003_logentry_add_action_flag_choices','2026-05-11 11:09:51.798346'),(19,'sessions','0001_initial','2026-05-11 11:09:51.860395'),(20,'accounts','0002_alter_user_username','2026-06-01 16:33:42.839793'),(22,'forum','0001_initial','2026-06-05 09:42:36.058648'),(23,'home','0001_initial','2026-06-12 08:55:10.574877'),(24,'formula','0001_initial','2026-07-07 10:04:53.917022'),(25,'shop','0001_initial','2026-07-08 15:18:25.853418'),(26,'forum','0002_postimage','2026-07-19 15:05:26.253983'),(27,'forum','0003_alter_postimage_post','2026-07-19 15:20:50.664031'),(28,'timer','0001_initial','2026-07-19 18:40:31.903171'),(29,'formula','0002_formula_view_count','2026-07-19 23:46:56.922994'),(30,'accounts','0003_alter_user_image','2026-07-24 09:18:38.642147'),(31,'formula','0003_alter_cubecategory_options_alter_cubestate_options_and_more','2026-07-24 14:05:10.586162'),(32,'forum','0004_alter_commentlike_options_alter_postcollect_options_and_more','2026-07-24 14:05:10.719662'),(33,'home','0002_banner','2026-07-24 14:05:11.091319'),(34,'shop','0002_alter_cart_options_alter_order_options_and_more','2026-07-24 14:05:11.168692'),(35,'timer','0002_alter_timerrecord_options','2026-07-24 14:05:11.194775'),(36,'shop','0003_address','2026-07-24 16:24:47.401734'),(37,'formula','0004_add_custom_category_fields','2026-07-29 09:25:48.148352'),(38,'accounts','0004_alter_user_username','2026-08-10 17:19:48.593559'),(39,'home','0003_add_user_navigation','2026-08-10 17:19:48.619320');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_cube_category`
--

DROP TABLE IF EXISTS `formula_cube_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_cube_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order` int NOT NULL,
  `method` varchar(50) NOT NULL,
  `phase` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `sort_order` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `is_custom` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `formula_cube_category_created_by_id_f4fc7195_fk_accounts_user_id` (`created_by_id`),
  CONSTRAINT `formula_cube_category_created_by_id_f4fc7195_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_cube_category`
--

LOCK TABLES `formula_cube_category` WRITE;
/*!40000 ALTER TABLE `formula_cube_category` DISABLE KEYS */;
INSERT INTO `formula_cube_category` VALUES (4,3,'CFOP','F2L','F2L','三阶魔方 CFOP 方法的 F2L 阶段',1,'2026-07-07 11:06:37.916198',NULL,0),(5,3,'CFOP','OLL','OLL','三阶魔方 CFOP 方法的 OLL 阶段',2,'2026-07-07 11:06:38.954387',NULL,0),(6,3,'CFOP','PLL','PLL','三阶魔方 CFOP 方法的 PLL 阶段',3,'2026-07-07 11:06:40.360197',NULL,0),(7,3,'CFOP','F2L','四向F2L','',0,'2026-07-29 09:46:27.782964',10,1);
/*!40000 ALTER TABLE `formula_cube_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_cube_state`
--

DROP TABLE IF EXISTS `formula_cube_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_cube_state` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `state_definition` json NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `category_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `formula_cube_state_category_id_cfeae333_fk_formula_c` (`category_id`),
  CONSTRAINT `formula_cube_state_category_id_cfeae333_fk_formula_c` FOREIGN KEY (`category_id`) REFERENCES `formula_cube_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_cube_state`
--

LOCK TABLES `formula_cube_state` WRITE;
/*!40000 ALTER TABLE `formula_cube_state` DISABLE KEYS */;
INSERT INTO `formula_cube_state` VALUES (1,'F2L完成状态','{\"faces\": {\"B\": [[\"gray\", \"gray\", \"gray\"], [\"green\", \"green\", \"green\"], [\"green\", \"green\", \"green\"]], \"D\": [[\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"]], \"F\": [[\"gray\", \"gray\", \"gray\"], [\"blue\", \"blue\", \"blue\"], [\"blue\", \"blue\", \"blue\"]], \"L\": [[\"gray\", \"gray\", \"gray\"], [\"orange\", \"orange\", \"orange\"], [\"orange\", \"orange\", \"orange\"]], \"R\": [[\"gray\", \"gray\", \"gray\"], [\"red\", \"red\", \"red\"], [\"red\", \"red\", \"red\"]], \"U\": [[\"gray\", \"gray\", \"gray\"], [\"gray\", \"gray\", \"gray\"], [\"gray\", \"gray\", \"gray\"]]}, \"description\": \"底层和前两层已完成，第三层和顶面为灰色\"}','底层和前两层已完成，顶层和第三层为灰色（未完成状态）','2026-07-08 09:24:25.364211',4),(2,'OLL完成状态','{\"faces\": {\"B\": [[\"gray\", \"gray\", \"gray\"], [\"green\", \"green\", \"green\"], [\"green\", \"green\", \"green\"]], \"D\": [[\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"]], \"F\": [[\"gray\", \"gray\", \"gray\"], [\"blue\", \"blue\", \"blue\"], [\"blue\", \"blue\", \"blue\"]], \"L\": [[\"gray\", \"gray\", \"gray\"], [\"orange\", \"orange\", \"orange\"], [\"orange\", \"orange\", \"orange\"]], \"R\": [[\"gray\", \"gray\", \"gray\"], [\"red\", \"red\", \"red\"], [\"red\", \"red\", \"red\"]], \"U\": [[\"yellow\", \"yellow\", \"yellow\"], [\"yellow\", \"yellow\", \"yellow\"], [\"yellow\", \"yellow\", \"yellow\"]]}, \"description\": \"底层、下面两层、顶面方向已完成，第三层待调整\"}','底层、前两层、顶面方向已完成，角块位置可能不正确','2026-07-08 09:24:25.420154',5),(3,'PLL完成状态','{\"faces\": {\"B\": [[\"green\", \"green\", \"green\"], [\"green\", \"green\", \"green\"], [\"green\", \"green\", \"green\"]], \"D\": [[\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"], [\"white\", \"white\", \"white\"]], \"F\": [[\"blue\", \"blue\", \"blue\"], [\"blue\", \"blue\", \"blue\"], [\"blue\", \"blue\", \"blue\"]], \"L\": [[\"orange\", \"orange\", \"orange\"], [\"orange\", \"orange\", \"orange\"], [\"orange\", \"orange\", \"orange\"]], \"R\": [[\"red\", \"red\", \"red\"], [\"red\", \"red\", \"red\"], [\"red\", \"red\", \"red\"]], \"U\": [[\"yellow\", \"yellow\", \"yellow\"], [\"yellow\", \"yellow\", \"yellow\"], [\"yellow\", \"yellow\", \"yellow\"]]}, \"description\": \"完全还原的魔方状态\"}','完全还原的魔方状态','2026-07-08 09:24:25.431265',6);
/*!40000 ALTER TABLE `formula_cube_state` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_formula`
--

DROP TABLE IF EXISTS `formula_formula`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_formula` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `notation` longtext NOT NULL,
  `inverse_notation` longtext NOT NULL,
  `pre_state_definition` json DEFAULT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  `difficulty` int NOT NULL,
  `description` longtext NOT NULL,
  `is_custom` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `target_state_id` bigint DEFAULT NULL,
  `view_count` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `formula_formula_category_id_2d7b2936_fk_formula_cube_category_id` (`category_id`),
  KEY `formula_formula_created_by_id_8d6b77d2_fk_accounts_user_id` (`created_by_id`),
  KEY `formula_formula_target_state_id_8022afe7_fk_formula_c` (`target_state_id`),
  CONSTRAINT `formula_formula_category_id_2d7b2936_fk_formula_cube_category_id` FOREIGN KEY (`category_id`) REFERENCES `formula_cube_category` (`id`),
  CONSTRAINT `formula_formula_created_by_id_8d6b77d2_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `formula_formula_target_state_id_8022afe7_fk_formula_c` FOREIGN KEY (`target_state_id`) REFERENCES `formula_cube_state` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=367 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_formula`
--

LOCK TABLES `formula_formula` WRITE;
/*!40000 ALTER TABLE `formula_formula` DISABLE KEYS */;
INSERT INTO `formula_formula` VALUES (239,'F2L-01','d\' L\' U L','L\' U\' L d',NULL,'formulas/F2L_Images/F2L_001.png',1,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.457998',4,NULL,1,6),(240,'F2L-02','U R U\' R\'','R U R\' U\'',NULL,'formulas/F2L_Images/F2L_002.png',1,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.490123',4,NULL,1,6),(241,'F2L-03','R U R\'','R U\' R\'',NULL,'formulas/F2L_Images/F2L_003.png',1,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.513833',4,NULL,1,4),(242,'F2L-04','y L\' U\' L','L\' U L y\'',NULL,'formulas/F2L_Images/F2L_004.png',1,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.537867',4,NULL,1,2),(243,'F2L-05','U\' R U R\' U R U R\'','R U\' R\' U\' R U\' R\' U',NULL,'formulas/F2L_Images/F2L_005.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.560667',4,NULL,1,0),(244,'F2L-06','U\' R U\' R\' U y\' R\' U\' R','R\' U R y U\' R U R\' U',NULL,'formulas/F2L_Images/F2L_006.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.590151',4,NULL,1,0),(245,'F2L-07','d R\' U\' R U\'2 R\' U R','R\' U\' R U\'2 R\' U R d\'',NULL,'formulas/F2L_Images/F2L_007.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.615940',4,NULL,1,2),(246,'F2L-08','U\' R U R\' U2 R U\' R\'','R U R\' U2 R U\' R\' U',NULL,'formulas/F2L_Images/F2L_008.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.639613',4,NULL,1,1),(247,'F2L-09','d R\' U\'2 R U\'2 R\' U R','R\' U\' R U\'2 R\' U\'2 R d\'',NULL,'formulas/F2L_Images/F2L_009.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.663288',4,NULL,1,0),(248,'F2L-10','U\' R U2 R\' U2 R U\' R\'','R U R\' U2 R U2 R\' U',NULL,'formulas/F2L_Images/F2L_010.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.687714',4,NULL,1,1),(249,'F2L-11','d\' L\' U2 L U\' L\' U L','L\' U\' L U L\' U2 L d',NULL,'formulas/F2L_Images/F2L_011.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.712758',4,NULL,1,0),(250,'F2L-12','U R U\'2 R\' U R U\' R\'','R U R\' U\' R U\'2 R\' U\'',NULL,'formulas/F2L_Images/F2L_012.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.739282',4,NULL,1,0),(251,'F2L-13','U\'2 R U R\' U R U\' R\'','R U R\' U\' R U\' R\' U\'2',NULL,'formulas/F2L_Images/F2L_013.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.764307',4,NULL,1,1),(252,'F2L-14','U2 y L\' U\' L U\' L\' U L','L\' U\' L U L\' U L y\' U2',NULL,'formulas/F2L_Images/F2L_014.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.787948',4,NULL,1,0),(253,'F2L-15','U R U R\' U\'2 R U R\'','R U\' R\' U\'2 R U\' R\' U\'',NULL,'formulas/F2L_Images/F2L_015.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.814302',4,NULL,1,0),(254,'F2L-16','(y) R\' D R U\' R\' D\' R','R\' D R U R\' D\' R (y)',NULL,'formulas/F2L_Images/F2L_016.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.838066',4,NULL,1,0),(255,'F2L-17','U y\' R\' U\' R d\' R U R\'','R U\' R\' d R\' U R y U\'',NULL,'formulas/F2L_Images/F2L_017.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.862327',4,NULL,1,0),(256,'F2L-18','U M\' U R U\' M U\' R\'','R U M\' U R\' U\' M U\'',NULL,'formulas/F2L_Images/F2L_018.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.886176',4,NULL,1,0),(257,'F2L-19','U R U\' R\' U R U\' R\' U R U\' R\'','R U R\' U\' R U R\' U\' R U R\' U\'',NULL,'formulas/F2L_Images/F2L_019.png',3,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.908505',4,NULL,1,0),(258,'F2L-20','U\' R\' F R F\' R U\' R\'','R U R\' F R\' F\' R U',NULL,'formulas/F2L_Images/F2L_020.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.933695',4,NULL,1,0),(259,'F2L-21','d\' L\' U L U L\' U\' L U L\' U\' L','L\' U L U\' L\' U L U\' L\' U\' L d',NULL,'formulas/F2L_Images/F2L_021.png',3,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.956637',4,NULL,1,0),(260,'F2L-22','d R\' U R U\' R\' U\' R','R\' U R U R\' U\' R d\'',NULL,'formulas/F2L_Images/F2L_022.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:00.982995',4,NULL,1,1),(261,'F2L-23','U R U\' R\' U\' R U R\' U\' R U R\'','R U\' R\' U R U\' R\' U R U R\' U\'',NULL,'formulas/F2L_Images/F2L_023.png',3,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.008466',4,NULL,1,0),(262,'F2L-24','U\' R U\' R\' U R U R\'','R U\' R\' U\' R U R\' U',NULL,'formulas/F2L_Images/F2L_024.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.033772',4,NULL,1,0),(263,'F2L-25','R U R\' U\'2 R U\' R\' U R U\' R\'','R U R\' U\' R U R\' U\'2 R U\' R\'',NULL,'formulas/F2L_Images/F2L_025.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.058387',4,NULL,1,0),(264,'F2L-26','U F R\' F\' R2 U\' R\' U2 R U\' R\'','R U R\' U2 R U R2 F R F\' U\'',NULL,'formulas/F2L_Images/F2L_026.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.084672',4,NULL,1,1),(265,'F2L-27','R U R\' U\'2 R U\' R\' U R U R\'','R U\' R\' U\' R U R\' U\'2 R U\' R\'',NULL,'formulas/F2L_Images/F2L_027.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.108187',4,NULL,1,0),(266,'F2L-28','R U R\' U\' R U2 R\' U\' R U R\'','R U\' R\' U R U2 R\' U R U\' R\'',NULL,'formulas/F2L_Images/F2L_028.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.132742',4,NULL,1,0),(267,'F2L-29','R U\' M\' U\' r\' U\'2 r U r\'','r U\' r\' U\'2 r U M U R\'',NULL,'formulas/F2L_Images/F2L_029.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.156001',4,NULL,1,0),(268,'F2L-30','r U\' r\' U\'2 r U M U R\'','R U\' M\' U\' r\' U\'2 r U r\'',NULL,'formulas/F2L_Images/F2L_030.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.179353',4,NULL,1,0),(269,'F2L-31','L D R\' F R F\' R U\' R\' U D\' L\'','L D U\' R U R\' F R\' F\' R D\' L\'',NULL,'formulas/F2L_Images/F2L_031.png',3,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.204262',4,NULL,1,0),(270,'F2L-32','y\' R\' U R U R\' U R U\' R\' U\' R','R\' U R U R\' U\' R U\' R\' U\' R y',NULL,'formulas/F2L_Images/F2L_032.png',3,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.227837',4,NULL,1,0),(271,'F2L-33','R U\' R\' U\' R U\' R\' U R U R\'','R U\' R\' U\' R U R\' U R U R\'',NULL,'formulas/F2L_Images/F2L_033.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.252616',4,NULL,1,3),(272,'F2L-34','y\' R\' U\'2 R U R\' U\' R','R\' U R U\' R\' U\'2 R y',NULL,'formulas/F2L_Images/F2L_034.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.278801',4,NULL,1,0),(273,'F2L-35','R U R\' U\'2 R U R\' U\' R U R\'','R U\' R\' U R U\' R\' U\'2 R U\' R\'',NULL,'formulas/F2L_Images/F2L_035.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.302506',4,NULL,1,0),(274,'F2L-36','R U2 R\' U\' R U R\'','R U\' R\' U R U2 R\'',NULL,'formulas/F2L_Images/F2L_036.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.327577',4,NULL,1,0),(275,'F2L-37','F U R U\' R\' F\' R U\' R\'','R U R\' F R U R\' U\' F\'',NULL,'formulas/F2L_Images/F2L_037.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.350824',4,NULL,1,0),(276,'F2L-38','y L\' U L U\' L\' U L','L\' U\' L U L\' U\' L y\'',NULL,'formulas/F2L_Images/F2L_038.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.374128',4,NULL,1,0),(277,'F2L-39','R U R\' U\' R U R\'','R U\' R\' U R U\' R\'',NULL,'formulas/F2L_Images/F2L_039.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.398335',4,NULL,1,0),(278,'F2L-40','R U\' R\' U R U\' R\'','R U R\' U\' R U R\'',NULL,'formulas/F2L_Images/F2L_040.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.422076',4,NULL,1,0),(279,'F2L-41','y L\' U\' L U L\' U\' L','L\' U L U\' L\' U L y\'',NULL,'formulas/F2L_Images/F2L_041.png',2,'F2L基础公式，用于构建前两层槽位',0,'2026-07-07 11:16:01.445118',4,NULL,1,0),(280,'OLL-01','R\' U2 R U R\' U R','R\' U\' R U\' R\' U2 R',NULL,'formulas/OLL_Images/OLL_001.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.471855',5,NULL,2,3),(281,'OLL-02','R U\' U\' R\' U\' R U\' R\'','R U R\' U R U U R\'',NULL,'formulas/OLL_Images/OLL_002.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.495499',5,NULL,2,0),(282,'OLL-03','r U R\' U\' r\' F R F\'','F R\' F\' r U R U\' r\'',NULL,'formulas/OLL_Images/OLL_003.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.519951',5,NULL,2,1),(283,'OLL-04','F\' r U R\' U\' r\' F R','R\' F\' r U R U\' r\' F',NULL,'formulas/OLL_Images/OLL_004.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.544489',5,NULL,2,0),(284,'OLL-05','R2 D\' R U\' U\' R\' D R U\' U\' R','R\' U U R\' D\' R U U R\' D R2',NULL,'formulas/OLL_Images/OLL_005.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.568181',5,NULL,2,0),(285,'OLL-06','R U U R\' U\' R U R\' U\' R U\' R\'','R U R\' U R U\' R\' U R U\' U\' R\'',NULL,'formulas/OLL_Images/OLL_006.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.594840',5,NULL,2,0),(286,'OLL-07','R U\' U\' R2\' U\' R2 U\' R2\' U2 R','R\' U2 R2\' U R2 U R2\' U U R\'',NULL,'formulas/OLL_Images/OLL_007.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.618263',5,NULL,2,0),(287,'OLL-08','F R U R\' U\' F\'','F U R U\' R\' F\'',NULL,'formulas/OLL_Images/OLL_008.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.642901',5,NULL,2,0),(288,'OLL-09','f R U R\' U\' f\'','f U R U\' R\' f\'',NULL,'formulas/OLL_Images/OLL_009.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.667501',5,NULL,2,0),(289,'OLL-10','B\' U\' R\' U R B','B\' R\' U\' R U B',NULL,'formulas/OLL_Images/OLL_010.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.693348',5,NULL,2,0),(290,'OLL-11','R U R\' U\' R\' F R F\'','F R\' F\' R U R U\' R\'',NULL,'formulas/OLL_Images/OLL_011.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.719952',5,NULL,2,0),(291,'OLL-12','F R U R\' U\'2 F\'','F U\'2 R U\' R\' F\'',NULL,'formulas/OLL_Images/OLL_012.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.745035',5,NULL,2,1),(292,'OLL-13','F\' L\' U\' L U2 F','F\' U2 L\' U L F',NULL,'formulas/OLL_Images/OLL_013.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.770396',5,NULL,2,0),(293,'OLL-14','f R U R\' U\'2 f\'','f U\'2 R U\' R\' f\'',NULL,'formulas/OLL_Images/OLL_014.png',1,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.796676',5,NULL,2,0),(294,'OLL-15','F R U R\' U\' F\' f R U R\' U\' f\'','f U R U\' R\' f\' F U R U\' R\' F\'',NULL,'formulas/OLL_Images/OLL_015.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.821571',5,NULL,2,0),(295,'OLL-16','f R U R\' U\' f\' U\' F R U R\' U\' F\'','F U R U\' R\' F\' U f U R U\' R\' f\'',NULL,'formulas/OLL_Images/OLL_016.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.847151',5,NULL,2,0),(296,'OLL-17','f R U R\' U\' f\' U F R U R\' U\' F\'','F U R U\' R\' F\' U\' f U R U\' R\' f\'',NULL,'formulas/OLL_Images/OLL_017.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.871964',5,NULL,2,0),(297,'OLL-18','R U\' U\' R2\' F R F\' U2 R\' F R F\'','F R\' F\' R U2 F R\' F\' R2\' U U R\'',NULL,'formulas/OLL_Images/OLL_018.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.896113',5,NULL,2,1),(298,'OLL-19','r\' U2 R U R\' U r','r\' U\' R U\' R\' U2 r',NULL,'formulas/OLL_Images/OLL_019.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.922978',5,NULL,2,0),(299,'OLL-20','r U\' U\' R\' U\' R U\' r\'','r U R\' U R U U r\'',NULL,'formulas/OLL_Images/OLL_020.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.947916',5,NULL,2,0),(300,'OLL-21','r U R\' U R U U r\'','r U\' U\' R\' U\' R U\' r\'',NULL,'formulas/OLL_Images/OLL_021.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.972274',5,NULL,2,0),(301,'OLL-22','r\' U\' R U\' R\' U2 r','r\' U2 R U R\' U r',NULL,'formulas/OLL_Images/OLL_022.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:01.997822',5,NULL,2,0),(302,'OLL-23','F R U\' R\' U\' R U R\' F\'','F R U\' R\' U R U R\' F\'',NULL,'formulas/OLL_Images/OLL_023.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.022701',5,NULL,2,0),(303,'OLL-24','R U\' U\' R2\' F R F\' R U\' U\' R\'','R U U R\' F R\' F\' R2\' U U R\'',NULL,'formulas/OLL_Images/OLL_024.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.047647',5,NULL,2,0),(304,'OLL-25','R B\' R2 F R2 B R2 F\' R','R\' F R2 B\' R2 F\' R2 B R\'',NULL,'formulas/OLL_Images/OLL_025.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.071970',5,NULL,2,0),(305,'OLL-26','R\' F R2 B\' R2 F\' R2 B R\'','R B\' R2 F R2 B R2 F\' R',NULL,'formulas/OLL_Images/OLL_026.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.096366',5,NULL,2,0),(306,'OLL-27','r\' U2 R U R\' U\' R U R\' U r','r\' U\' R U\' R\' U R U\' R\' U2 r',NULL,'formulas/OLL_Images/OLL_027.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.121666',5,NULL,2,0),(307,'OLL-28','r U R\' U R U\'2 r\'','r U\'2 R\' U\' R U\' r\'',NULL,'formulas/OLL_Images/OLL_028.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.146607',5,NULL,2,0),(308,'OLL-29','R U R\' U R\' F R F\' U2 R\' F R F\'','F R\' F\' R U2 F R\' F\' R U\' R U\' R\'',NULL,'formulas/OLL_Images/OLL_029.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.171188',5,NULL,2,0),(309,'OLL-30','F R U R\' U y\' R\' U2 R\' F R F\'','F R\' F\' R U2 R y U\' R U\' R\' F\'',NULL,'formulas/OLL_Images/OLL_030.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.197033',5,NULL,2,0),(310,'OLL-31','M下 U R U R\' U\' M上 R\' F R F\'','F R\' F\' R M上 U R U\' R\' U\' M下',NULL,'formulas/OLL_Images/OLL_031.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.222481',5,NULL,2,0),(311,'OLL-32','R U R\' U\' R\' F R2 U R\' U\' F\'','F U R U\' R2 F\' R U R U\' R\'',NULL,'formulas/OLL_Images/OLL_032.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.400894',5,NULL,2,0),(312,'OLL-33','R U R\' U R\' F R F\' R U\' U\' R\'','R U U R\' F R\' F\' R U\' R U\' R\'',NULL,'formulas/OLL_Images/OLL_033.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.425549',5,NULL,2,0),(313,'OLL-34','r U R\' U\' r\' R U R U\' R\'','R U R\' U\' R\' r U R U\' r\'',NULL,'formulas/OLL_Images/OLL_034.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.449391',5,NULL,2,0),(314,'OLL-35','R U R\' U\' r R\' U R U\' r\'','r U R\' U\' R r\' U R U\' R\'',NULL,'formulas/OLL_Images/OLL_035.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.475651',5,NULL,2,0),(315,'OLL-36','R\' U\' R\' F R F\' U R','R\' U\' F R\' F\' R U R',NULL,'formulas/OLL_Images/OLL_036.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.500355',5,NULL,2,0),(316,'OLL-37','R U R\' U\' x D\' R\' U R E\'','E R\' U\' R D x\' U R U\' R\'',NULL,'formulas/OLL_Images/OLL_037.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.525317',5,NULL,2,0),(317,'OLL-38','R U R\' U R U\' R\' U\' R\' F R F\'','F R\' F\' R U R U R\' U\' R U\' R\'',NULL,'formulas/OLL_Images/OLL_038.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.551326',5,NULL,2,0),(318,'OLL-39','R\' U\' R U\' R\' U R U l U\' R\' U','U\' R U l\' U\' R\' U\' R U R\' U R',NULL,'formulas/OLL_Images/OLL_039.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.577062',5,NULL,2,0),(319,'OLL-40','F R U R\' U\' F\' U F R U R\' U\' F\'','F U R U\' R\' F\' U\' F U R U\' R\' F\'',NULL,'formulas/OLL_Images/OLL_040.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.604400',5,NULL,2,0),(320,'OLL-41','r U R\' U R\' F R F\' R U2 r\'','r U2 R\' F R\' F\' R U\' R U\' r\'',NULL,'formulas/OLL_Images/OLL_041.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.628991',5,NULL,2,0),(321,'OLL-42','R U B\' U\' R\' U R B R\'','R B\' R\' U\' R U B U\' R\'',NULL,'formulas/OLL_Images/OLL_042.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.653055',5,NULL,2,0),(322,'OLL-43','R\' U\' F U R U\' R\' F\' R','R\' F R U R\' U\' F\' U R',NULL,'formulas/OLL_Images/OLL_043.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.679334',5,NULL,2,0),(323,'OLL-44','R\' F R U R\' U\' F\' U R','R\' U\' F U R U\' R\' F\' R',NULL,'formulas/OLL_Images/OLL_044.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.706333',5,NULL,2,0),(324,'OLL-45','L F\' L\' U\' L U F U\' L\'','L U F\' U\' L\' U L F L\'',NULL,'formulas/OLL_Images/OLL_045.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.733863',5,NULL,2,0),(325,'OLL-46','R U R\' U R U2 R\' F R U R\' U\' F\'','F U R U\' R\' F\' R U2 R\' U\' R U\' R\'',NULL,'formulas/OLL_Images/OLL_046.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.759797',5,NULL,2,0),(326,'OLL-47','R\' U\' R U\' R\' U2 R F R U R\' U\' F\'','F U R U\' R\' F\' R\' U2 R U R\' U R',NULL,'formulas/OLL_Images/OLL_047.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.783965',5,NULL,2,0),(327,'OLL-48','r\' U2 R U R\' U r R U2 R\' U\' R U\' R\'','R U R\' U R U2 R\' r\' U\' R U\' R\' U2 r',NULL,'formulas/OLL_Images/OLL_048.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.809238',5,NULL,2,0),(328,'OLL-49','r U2 R\' U\' R U\' r\' R\' U2 R U R\' U R','R\' U\' R U\' R\' U2 R r U R\' U R U2 r\'',NULL,'formulas/OLL_Images/OLL_049.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.834973',5,NULL,2,0),(329,'OLL-50','r U r\' R U R\' U\' r U\' r\'','r U r\' U R U\' R\' r U\' r\'',NULL,'formulas/OLL_Images/OLL_050.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.860147',5,NULL,2,0),(330,'OLL-51','l\' U\' l L\' U\' L U l\' U l','l\' U\' l U\' L\' U L l\' U l',NULL,'formulas/OLL_Images/OLL_051.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.885634',5,NULL,2,0),(331,'OLL-52','R\' F R U R\' F\' R y\' R U\' R\'','R U R\' y R\' F R U\' R\' F\' R',NULL,'formulas/OLL_Images/OLL_052.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.910330',5,NULL,2,0),(332,'OLL-53','F U R U\' R2\' F\' R U R U\' R\'','R U R\' U\' R\' F R2\' U R\' U\' F\'',NULL,'formulas/OLL_Images/OLL_053.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.935872',5,NULL,2,0),(333,'OLL-54','R\' U\' R U\' R\' U y\' R\' U R B','B\' R\' U\' R y U\' R U R\' U R',NULL,'formulas/OLL_Images/OLL_054.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.961488',5,NULL,2,0),(334,'OLL-55','r U r\' U R U\' R\'2 r U\' r\'','r U r\' R\'2 U R\' U\' r U\' r\'',NULL,'formulas/OLL_Images/OLL_055.png',2,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:02.986595',5,NULL,2,0),(335,'OLL-56','R\' F U R U\' R2\' F\' R2 U R\' U\' R','R\' U R U\' R2 F R2\' U R\' U\' F\' R',NULL,'formulas/OLL_Images/OLL_056.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:03.012450',5,NULL,2,0),(336,'OLL-57','r\' R U R U R\' U\' r2 R2\' U R U\' r\'','r U R\' U\' R2\' r2 U R U\' R\' U\' R\' r',NULL,'formulas/OLL_Images/OLL_057.png',3,'OLL公式，用于调整顶层朝向',0,'2026-07-07 11:16:03.037768',5,NULL,2,0),(337,'PLL-01','R U\' R U R U R U\' R\' U\' R2','R2 U R U R\' U\' R\' U\' R\' U R\'',NULL,'formulas/PLL_Images/PLL_001.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.063289',6,NULL,3,0),(338,'PLL-02','R2\' U R U R\' U\' R\' U\' R\' U R\'','R U\' R U R U R U\' R\' U\' R2\'',NULL,'formulas/PLL_Images/PLL_002.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.088700',6,NULL,3,0),(339,'PLL-03','M2 U M2 U2 M2 U M2','M2 U\' M2 U2 M2 U\' M2',NULL,'formulas/PLL_Images/PLL_003.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.113706',6,NULL,3,0),(340,'PLL-04','M2 U M2 U M上 U2 M2 U2 M上 U2','U2 M上 U2 M2 U2 M上 U\' M2 U\' M2',NULL,'formulas/PLL_Images/PLL_004.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.137423',6,NULL,3,0),(341,'PLL-05','R2 D2 R\' U\' R D2 R\' U R\'','R U\' R D2 R\' U R D2 R2',NULL,'formulas/PLL_Images/PLL_005.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.161096',6,NULL,3,0),(342,'PLL-06','R U\' R D2 R\' U R D2 R2','R2 D2 R\' U\' R D2 R\' U R\'',NULL,'formulas/PLL_Images/PLL_006.png',2,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.185743',6,NULL,3,0),(343,'PLL-07','R2 U R\' U\' y R U R\' U\'2 R U R\' y\' R U\' R2','R2 U R\' y R U\' R\' U\'2 R U\' R\' y\' U R U\' R2',NULL,'formulas/PLL_Images/PLL_007.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.211944',6,NULL,3,0),(344,'PLL-08','R U R\' U\' R\' F R2 U\' R\' U\' R U R\' F\'','F R U\' R\' U R U R2 F\' R U R U\' R\'',NULL,'formulas/PLL_Images/PLL_008.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.236281',6,NULL,3,0),(345,'PLL-09','R U R\' F\' R U R\' U\' R\' F R2 U\' R\' U\'','U R U R2 F\' R U R U\' R\' F R U\' R\'',NULL,'formulas/PLL_Images/PLL_009.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.260731',6,NULL,3,0),(346,'PLL-10','z U\' R D\' R2 U R\' U\' R2 U D R\'','R D\' U\' R2 U R U\' R2 D R\' U z\'',NULL,'formulas/PLL_Images/PLL_010.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.286508',6,NULL,3,0),(347,'PLL-11','F R U\' R\' U\' R U R\' F\' R U R\' U\' R\' F R F\'','F R\' F\' R U R U\' R\' F R U\' R\' U R U R\' F\'',NULL,'formulas/PLL_Images/PLL_011.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.311161',6,NULL,3,0),(348,'PLL-12','U\' R\' U R U\' R2\' b\' x R\' U R y\' R U R\' U\' R2','R2 U R U\' R\' y R\' U\' R x\' b R2\' U R\' U\' R U',NULL,'formulas/PLL_Images/PLL_012.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.337153',6,NULL,3,0),(349,'PLL-13','R\' U R\' d\' R\' F\' R2 U\' R\' U R\' F R F','F\' R\' F\' R U\' R U R2 F R d R U\' R',NULL,'formulas/PLL_Images/PLL_013.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.362022',6,NULL,3,0),(350,'PLL-14','R U\' U\' R\' U2 R B\' R\' U\' R U R B R2\' U','U\' R2\' B\' R\' U\' R\' U R B R\' U2 R U U R\'',NULL,'formulas/PLL_Images/PLL_014.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.387408',6,NULL,3,0),(351,'PLL-15','R\' U2 R U\' U\' R\' F R U R\' U\' R\' F\' R2 U\'','U R2 F R U R U\' R\' F\' R U U R\' U2 R',NULL,'formulas/PLL_Images/PLL_015.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.412579',6,NULL,3,0),(352,'PLL-16','z R\' U R\' z\' R U2 L\' U R\' z U R\' z\' R U2 L\' U R\'','R U\' L U2 R\' z R U\' z\' R U\' L U2 R\' z R U\' R z\'',NULL,'formulas/PLL_Images/PLL_016.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.435580',6,NULL,3,0),(353,'PLL-17','z U\' R D\' R2 U R\' U\' z\' R U R\' z R2 U R\' D R\'','R D\' R U\' R2 z\' R U\' R\' z U R U\' R2 D R\' U z\'',NULL,'formulas/PLL_Images/PLL_017.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.460190',6,NULL,3,0),(354,'PLL-18','R2\' u\' R U\' R U R\' u R2\' y R U\' R\'','R U R\' y\' R2\' u\' R U\' R\' U R\' u R2\'',NULL,'formulas/PLL_Images/PLL_018.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.486181',6,NULL,3,0),(355,'PLL-19','R U R\' y\' R2\' u\' R U\' R\' U R\' u R2','R2 u\' R U\' R U R\' u R2\' y R U\' R\'',NULL,'formulas/PLL_Images/PLL_019.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.511134',6,NULL,3,0),(356,'PLL-20','R2\' u R\' U R\' U\' R u\' R2\' y\' R\' U R','R\' U\' R y R2\' u R\' U R U\' R u\' R2\'',NULL,'formulas/PLL_Images/PLL_020.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.537408',6,NULL,3,0),(357,'PLL-21','R\' d\' F R2\' u R\' U R U\' R u\' R2','R2 u R\' U R\' U\' R u\' R2\' F\' d R',NULL,'formulas/PLL_Images/PLL_021.png',3,'PLL公式，用于调整顶层位置',0,'2026-07-07 11:16:03.561603',6,NULL,3,0),(360,'F2L-31-BR','R\' U R\' F R F\' U R U2 R\' U R','R\' U\' R U2 R\' U\' F R\' F\' R U\' R',NULL,'formula_thumbnails/upload_thumbnail_TQWFffl.webp',3,'',1,'2026-07-28 10:07:26.658056',7,10,1,19),(361,'f2l-test','U\' r U\' R\' U R U r\'','r U\' R\' U\' R U r\' U',NULL,'formula_thumbnails/upload_thumbnail.webp',2,'test',1,'2026-08-17 10:57:48.808354',4,17,1,4),(362,'f2l-test2','U r U\' r\' U\' L U F L\'','L F\' U\' L\' U r U r\' U\'',NULL,'formula_thumbnails/upload_thumbnail_8JIHTQR.webp',2,'',1,'2026-08-17 14:26:12.807472',4,17,1,1),(363,'F2L-33-FL','r U r\' U\' r\' F r F\'','F r\' F\' r U r U\' r\'',NULL,'formula_thumbnails/upload_thumbnail_oRs5grb.webp',2,'',1,'2026-08-18 07:27:32.226169',7,10,1,12),(364,'F2L-07-FR','U\'  r U\' R\' U R U r\'','r U\' R\' U\' R U r\' U',NULL,'formula_thumbnails/upload_thumbnail_wq0n08e.webp',2,'',1,'2026-08-18 07:35:28.956940',7,10,1,14),(365,'F2L-14-FR','r U\' r\' U2 r U r\'','r U\' r\' U2 r U r\'',NULL,'formula_thumbnails/upload_thumbnail_ohBkJ2v.webp',2,'',1,'2026-08-18 07:47:32.763781',7,10,1,3),(366,'F2L-10-BR','R2 F\' U\' F U R2','R2 U\' F\' U F R2',NULL,'formulas/F2L_Images/F2L_010.png',2,'',1,'2026-08-18 08:37:07.914460',4,10,1,11);
/*!40000 ALTER TABLE `formula_formula` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_formula_collection`
--

DROP TABLE IF EXISTS `formula_formula_collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_formula_collection` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `formula_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `formula_formula_collection_user_id_formula_id_4d365c61_uniq` (`user_id`,`formula_id`),
  KEY `formula_formula_coll_formula_id_81ad47ba_fk_formula_f` (`formula_id`),
  CONSTRAINT `formula_formula_coll_formula_id_81ad47ba_fk_formula_f` FOREIGN KEY (`formula_id`) REFERENCES `formula_formula` (`id`),
  CONSTRAINT `formula_formula_collection_user_id_0acb4f8b_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_formula_collection`
--

LOCK TABLES `formula_formula_collection` WRITE;
/*!40000 ALTER TABLE `formula_formula_collection` DISABLE KEYS */;
INSERT INTO `formula_formula_collection` VALUES (1,'2026-07-08 13:56:42.438514',239,1),(11,'2026-07-24 14:22:46.224749',297,1),(12,'2026-08-17 08:26:31.622927',360,10),(15,'2026-08-18 07:31:39.855433',363,10),(16,'2026-08-18 07:44:15.241766',364,10),(17,'2026-08-18 07:48:57.597638',365,10),(18,'2026-08-18 11:05:16.169305',364,17),(19,'2026-08-18 11:05:17.286529',365,17);
/*!40000 ALTER TABLE `formula_formula_collection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_formula_tag`
--

DROP TABLE IF EXISTS `formula_formula_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_formula_tag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `color` varchar(7) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_formula_tag`
--

LOCK TABLES `formula_formula_tag` WRITE;
/*!40000 ALTER TABLE `formula_formula_tag` DISABLE KEYS */;
INSERT INTO `formula_formula_tag` VALUES (7,'F2L','#1890ff','2026-07-07 11:06:37.936320'),(8,'基础','#1890ff','2026-07-07 11:06:37.954817'),(9,'OLL','#1890ff','2026-07-07 11:06:38.969239'),(10,'常用','#1890ff','2026-07-07 11:06:38.982746'),(11,'PLL','#1890ff','2026-07-07 11:06:40.372673'),(12,'进阶','#1890ff','2026-07-07 11:06:40.385177');
/*!40000 ALTER TABLE `formula_formula_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_formula_tag_relation`
--

DROP TABLE IF EXISTS `formula_formula_tag_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_formula_tag_relation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `formula_id` bigint NOT NULL,
  `tag_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `formula_formula_tag_relation_formula_id_tag_id_59674866_uniq` (`formula_id`,`tag_id`),
  KEY `formula_formula_tag__tag_id_9b5262c7_fk_formula_f` (`tag_id`),
  CONSTRAINT `formula_formula_tag__formula_id_2e32b839_fk_formula_f` FOREIGN KEY (`formula_id`) REFERENCES `formula_formula` (`id`),
  CONSTRAINT `formula_formula_tag__tag_id_9b5262c7_fk_formula_f` FOREIGN KEY (`tag_id`) REFERENCES `formula_formula_tag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=715 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_formula_tag_relation`
--

LOCK TABLES `formula_formula_tag_relation` WRITE;
/*!40000 ALTER TABLE `formula_formula_tag_relation` DISABLE KEYS */;
INSERT INTO `formula_formula_tag_relation` VALUES (477,239,7),(478,239,8),(479,240,7),(480,240,8),(481,241,7),(482,241,8),(483,242,7),(484,242,8),(485,243,7),(486,243,8),(487,244,7),(488,244,8),(489,245,7),(490,245,8),(491,246,7),(492,246,8),(493,247,7),(494,247,8),(495,248,7),(496,248,8),(497,249,7),(498,249,8),(499,250,7),(500,250,8),(501,251,7),(502,251,8),(503,252,7),(504,252,8),(505,253,7),(506,253,8),(507,254,7),(508,254,8),(509,255,7),(510,255,8),(511,256,7),(512,256,8),(513,257,7),(514,257,8),(515,258,7),(516,258,8),(517,259,7),(518,259,8),(519,260,7),(520,260,8),(521,261,7),(522,261,8),(523,262,7),(524,262,8),(525,263,7),(526,263,8),(527,264,7),(528,264,8),(529,265,7),(530,265,8),(531,266,7),(532,266,8),(533,267,7),(534,267,8),(535,268,7),(536,268,8),(537,269,7),(538,269,8),(539,270,7),(540,270,8),(541,271,7),(542,271,8),(543,272,7),(544,272,8),(545,273,7),(546,273,8),(547,274,7),(548,274,8),(549,275,7),(550,275,8),(551,276,7),(552,276,8),(553,277,7),(554,277,8),(555,278,7),(556,278,8),(557,279,7),(558,279,8),(559,280,9),(560,280,10),(561,281,9),(562,281,10),(563,282,9),(564,282,10),(565,283,9),(566,283,10),(567,284,9),(568,284,10),(569,285,9),(570,285,10),(571,286,9),(572,286,10),(573,287,9),(574,287,10),(575,288,9),(576,288,10),(577,289,9),(578,289,10),(579,290,9),(580,290,10),(581,291,9),(582,291,10),(583,292,9),(584,292,10),(585,293,9),(586,293,10),(587,294,9),(588,294,10),(589,295,9),(590,295,10),(591,296,9),(592,296,10),(593,297,9),(594,297,10),(595,298,9),(596,298,10),(597,299,9),(598,299,10),(599,300,9),(600,300,10),(601,301,9),(602,301,10),(603,302,9),(604,302,10),(605,303,9),(606,303,10),(607,304,9),(608,304,10),(609,305,9),(610,305,10),(611,306,9),(612,306,10),(613,307,9),(614,307,10),(615,308,9),(616,308,10),(617,309,9),(618,309,10),(619,310,9),(620,310,10),(621,311,9),(622,311,10),(623,312,9),(624,312,10),(625,313,9),(626,313,10),(627,314,9),(628,314,10),(629,315,9),(630,315,10),(631,316,9),(632,316,10),(633,317,9),(634,317,10),(635,318,9),(636,318,10),(637,319,9),(638,319,10),(639,320,9),(640,320,10),(641,321,9),(642,321,10),(643,322,9),(644,322,10),(645,323,9),(646,323,10),(647,324,9),(648,324,10),(649,325,9),(650,325,10),(651,326,9),(652,326,10),(653,327,9),(654,327,10),(655,328,9),(656,328,10),(657,329,9),(658,329,10),(659,330,9),(660,330,10),(661,331,9),(662,331,10),(663,332,9),(664,332,10),(665,333,9),(666,333,10),(667,334,9),(668,334,10),(669,335,9),(670,335,10),(671,336,9),(672,336,10),(673,337,11),(674,337,12),(675,338,11),(676,338,12),(677,339,11),(678,339,12),(679,340,11),(680,340,12),(681,341,11),(682,341,12),(683,342,11),(684,342,12),(685,343,11),(686,343,12),(687,344,11),(688,344,12),(689,345,11),(690,345,12),(691,346,11),(692,346,12),(693,347,11),(694,347,12),(695,348,11),(696,348,12),(697,349,11),(698,349,12),(699,350,11),(700,350,12),(701,351,11),(702,351,12),(703,352,11),(704,352,12),(705,353,11),(706,353,12),(707,354,11),(708,354,12),(709,355,11),(710,355,12),(711,356,11),(712,356,12),(713,357,11),(714,357,12);
/*!40000 ALTER TABLE `formula_formula_tag_relation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_comment`
--

DROP TABLE IF EXISTS `forum_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `like_count` int NOT NULL,
  `dislike_count` int NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `is_hidden` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` bigint NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  `post_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `forum_comment_author_id_9e60eecd_fk_accounts_user_id` (`author_id`),
  KEY `forum_comment_parent_id_4c29b530_fk_forum_comment_id` (`parent_id`),
  KEY `forum_comment_post_id_eb329692_fk_forum_post_id` (`post_id`),
  KEY `forum_comment_created_at_13bd6261` (`created_at`),
  CONSTRAINT `forum_comment_author_id_9e60eecd_fk_accounts_user_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `forum_comment_parent_id_4c29b530_fk_forum_comment_id` FOREIGN KEY (`parent_id`) REFERENCES `forum_comment` (`id`),
  CONSTRAINT `forum_comment_post_id_eb329692_fk_forum_post_id` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_comment`
--

LOCK TABLES `forum_comment` WRITE;
/*!40000 ALTER TABLE `forum_comment` DISABLE KEYS */;
INSERT INTO `forum_comment` VALUES (1,'这篇教程太棒了！终于弄懂了F2L！',0,0,0,0,'2026-06-05 16:38:15.636398','2026-06-05 16:38:15.636471',10,NULL,1),(2,'这篇教程太棒了！终于弄懂了F2L！',1,0,0,0,'2026-06-05 16:39:09.723151','2026-06-05 16:39:09.723173',10,NULL,2),(3,'不客气，能帮到你就好！',0,0,0,0,'2026-06-05 16:42:12.815752','2026-06-05 16:42:12.815774',10,2,2),(4,'终于把帖子显示整好了',1,0,0,0,'2026-06-05 19:48:18.691713','2026-06-05 19:48:18.693265',10,NULL,3),(5,'有问题',0,0,0,0,'2026-06-07 10:53:49.988151','2026-06-07 10:53:49.988182',10,2,2),(6,'@bh08 修复好了',0,0,0,0,'2026-06-07 11:05:17.263818','2026-06-07 11:05:17.263878',10,2,2),(7,'评论1',1,0,0,0,'2026-06-07 11:06:55.287366','2026-06-07 11:06:55.287414',10,NULL,2),(8,'评论评论的评论',0,0,0,0,'2026-06-07 11:13:45.186605','2026-06-07 11:13:45.187359',10,2,2),(9,'评论1',0,1,0,0,'2026-06-10 08:48:40.548613','2026-06-10 08:48:40.549955',10,NULL,4),(10,'@bh08 三级评论',0,0,0,0,'2026-06-10 15:01:49.730104','2026-06-10 15:01:49.731232',10,3,2),(11,'@bh08 还是有问题',0,0,0,0,'2026-06-10 15:14:38.564634','2026-06-10 15:14:38.564761',10,5,2),(12,'二级评论1',0,0,0,0,'2026-06-10 15:46:12.260231','2026-06-10 15:46:12.260288',10,7,2),(13,'回复评论的评论',0,0,0,0,'2026-06-10 15:46:32.789705','2026-06-10 15:46:32.789724',10,12,2),(14,'你好1',1,0,0,0,'2026-06-10 15:51:11.133073','2026-06-10 15:51:11.133114',10,4,3),(15,'你好2',1,0,0,0,'2026-06-10 15:51:21.108307','2026-06-10 15:51:21.108343',10,14,3);
/*!40000 ALTER TABLE `forum_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_comment_like`
--

DROP TABLE IF EXISTS `forum_comment_like`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_comment_like` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `is_like` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `comment_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `forum_comment_like_comment_id_user_id_d60aefe4_uniq` (`comment_id`,`user_id`),
  KEY `forum_comment_like_user_id_d8a40fcd_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `forum_comment_like_comment_id_b7b768e7_fk_forum_comment_id` FOREIGN KEY (`comment_id`) REFERENCES `forum_comment` (`id`),
  CONSTRAINT `forum_comment_like_user_id_d8a40fcd_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_comment_like`
--

LOCK TABLES `forum_comment_like` WRITE;
/*!40000 ALTER TABLE `forum_comment_like` DISABLE KEYS */;
INSERT INTO `forum_comment_like` VALUES (36,1,'2026-06-10 14:50:32.478033',2,10),(38,1,'2026-06-10 15:48:20.216659',7,10),(40,1,'2026-06-10 15:51:13.022254',14,10),(41,1,'2026-06-10 15:51:22.942431',15,10),(42,0,'2026-07-19 15:31:36.696956',9,10),(43,1,'2026-08-18 08:19:42.933607',4,10);
/*!40000 ALTER TABLE `forum_comment_like` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_post`
--

DROP TABLE IF EXISTS `forum_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_post` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `content` longtext NOT NULL,
  `content_md` longtext NOT NULL,
  `view_count` int NOT NULL,
  `like_count` int NOT NULL,
  `comment_count` int NOT NULL,
  `collect_count` int NOT NULL,
  `is_pinned` tinyint(1) NOT NULL,
  `is_essence` tinyint(1) NOT NULL,
  `is_closed` tinyint(1) NOT NULL,
  `status` varchar(20) NOT NULL,
  `report_count` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `author_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `forum_post_author__f7ff0a_idx` (`author_id`,`created_at` DESC),
  KEY `forum_post_created_543ce4_idx` (`created_at` DESC),
  KEY `forum_post_status_56aec8_idx` (`status`,`created_at` DESC),
  KEY `forum_post_title_d13f3075` (`title`),
  KEY `forum_post_created_at_ecff5f37` (`created_at`),
  CONSTRAINT `forum_post_author_id_609b7963_fk_accounts_user_id` FOREIGN KEY (`author_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_post`
--

LOCK TABLES `forum_post` WRITE;
/*!40000 ALTER TABLE `forum_post` DISABLE KEYS */;
INSERT INTO `forum_post` VALUES (1,'【新手必看】三阶魔方零基础入门教程','# 三阶魔方零基础入门教程\n\n## 前言\n魔方并不难，只要掌握了方法，任何人都可以学会还原三阶魔方。\n\n## 第一步：底层十字\n在底面拼出一个白色十字，且棱块侧面颜色与中心块对齐。\n\n## 第二步：底层角块\n完成白色面，同时底层四周颜色对齐。\n\n## 第三步：中层棱块\n还原第二层（中间层）的四个棱块。\n\n## 第四步：顶层十字\n在顶层拼出黄色十字。\n\n## 第五步：顶层面位\n将顶层全部变成黄色。\n\n## 第六步：顶层角块归位\n调整顶层角块位置。\n\n## 第七步：顶层棱块归位\n最后一步，完成整个魔方！\n\n祝大家早日学会魔方！🎉','',5,1,1,0,1,1,0,'published',0,'2026-06-05 09:55:10.802878','2026-06-05 09:55:10.802918',11),(2,'CFOP速拧教程 - F2L理解法','# CFOP进阶教程：F2L理解法\n\n## 什么是F2L？\nF2L（First Two Layers）是CFOP速拧法的第二步，指同时还原前两层。\n\n## 核心思想\nF2L的本质是把一对\"角块+棱块\"组合起来放入正确的位置。\n\n## 常用F2L公式\n\n| 情况 | 公式 |\n|------|------|\n| 角棱相连 | `U R U\' R\'` |\n| 角棱分离 | `R U R\'` |\n| 角棱背面 | `R U2 R\' U R U R\'` |\n\n## 练习技巧\n1. 慢速练习，理解原理\n2. 找规律，观察相对位置\n3. 预判下一组\n\nF2L熟练后，成绩可轻松进入30秒！💪','',50,2,10,1,0,1,0,'published',0,'2026-06-05 09:55:10.823840','2026-06-05 09:55:10.823875',11),(3,'魔方公式记忆技巧分享','# 魔方公式记忆技巧\n\n## 肌肉记忆法\n不要死记硬背公式字母，而是通过反复练习形成肌肉记忆。\n\n## 分段记忆\n将长公式分成几个小段，逐段练习后连接。\n\n## 镜像对称\n很多公式是左右对称的，记住一个就能推导出另一个。\n\n## 故事联想\n为公式中的转动编一个故事，帮助记忆。\n\n## 每天10分钟\n坚持每天练习，比一次性练很久效果更好。\n\n大家有什么好的记忆方法？欢迎分享！','',17,1,3,1,0,0,0,'published',0,'2026-06-05 09:55:10.841141','2026-06-05 09:55:10.841164',11),(4,'三阶魔方CFOP教程新标题','这是教程内容，使用Markdown格式\r\n![bh01_cropped](/media/forum/posts/2026/08/bh01_cropped_compressed.webp)','',40,2,1,0,0,0,0,'published',0,'2026-06-05 09:56:27.071163','2026-08-18 08:06:46.898068',10),(5,'发布新帖子','# 魔方\r\n## 标题二\r\n### 标题三\r\n```\r\n公式如下\r\npython\r\n```','',31,1,0,1,0,0,0,'deleted',0,'2026-06-12 10:08:08.741039','2026-06-12 10:52:53.080432',10),(6,'再发一篇新帖子（修改）','# CFOP 速拧学习方法\r\n\r\n## 什么是 CFOP？\r\n\r\nCFOP 是目前最主流的魔方速拧解法，由四个步骤组成：\r\n\r\n1. **C（Cross）**——底面十字\r\n2. **F（F2L）**——前两层\r\n3. **O（OLL）**——顶面朝向\r\n4. **P（PLL）**——顶层排列\r\n\r\n## 学习顺序建议\r\n\r\n| 阶段 | 内容                                 | 目标时间 |\r\n| ---- | ------------------------------------ | -------- |\r\n| 入门 | C + 4个基本公式                      | 60秒     |\r\n| 进阶 | F2L理解法 + 7个十字OLL + 4个PLL      | 30秒     |\r\n| 熟练 | F2L 41种情况 + 全部OLL(57) + PLL(21) | 15秒内   |\r\n\r\n## 实用技巧\r\n\r\n- **C**：八步内完成十字，学会盲拧预判\r\n- **F2L**：先理解“藏角藏棱”原理，不建议死记公式\r\n- **OLL**：先学十字后的7条，其他慢慢补充\r\n- **PLL**：优先学三棱换、三角换、邻角对棱换等高频公式\r\n\r\n## 资源推荐\r\n\r\n- 网站：`algdb.net` 公式库\r\n- 视频：J Perm 教学频道\r\n- App：Cube Station 计时练习\r\n\r\n> 每天练习20分钟，两个月基本可以进30秒。公式不是越多越好，**指法流畅**比记全更重要。','',4,0,0,0,0,0,0,'deleted',0,'2026-06-12 10:25:11.426914','2026-06-12 10:47:10.140862',10),(7,'返回格式测试','这是教程内容，使用Markdown格式...','',1,0,0,0,0,0,0,'deleted',0,'2026-06-12 10:28:11.697133','2026-06-12 10:28:11.697157',10),(8,'再发一篇新帖子2修改','# CFOP 速拧学习方法\r\n\r\n## 什么是 CFOP？\r\n\r\nCFOP 是目前最主流的魔方速拧解法，由四个步骤组成：\r\n\r\n1. **C（Cross）**——底面十字\r\n2. **F（F2L）**——前两层\r\n3. **O（OLL）**——顶面朝向\r\n4. **P（PLL）**——顶层排列\r\n\r\n## 学习顺序建议\r\n\r\n| 阶段 | 内容                                 | 目标时间 |\r\n| ---- | ------------------------------------ | -------- |\r\n| 入门 | C + 4个基本公式                      | 60秒     |\r\n| 进阶 | F2L理解法 + 7个十字OLL + 4个PLL      | 30秒     |\r\n| 熟练 | F2L 41种情况 + 全部OLL(57) + PLL(21) | 15秒内   |\r\n\r\n## 实用技巧\r\n\r\n- **C**：八步内完成十字，学会盲拧预判\r\n- **F2L**：先理解“藏角藏棱”原理，不建议死记公式\r\n- **OLL**：先学十字后的7条，其他慢慢补充\r\n- **PLL**：优先学三棱换、三角换、邻角对棱换等高频公式\r\n\r\n## 资源推荐\r\n\r\n- 网站：`algdb.net` 公式库\r\n- 视频：J Perm 教学频道\r\n- App：Cube Station 计时练习\r\n\r\n> 每天练习20分钟，两个月基本可以进30秒。公式不是越多越好，**指法流畅**比记全更重要。','',5,0,0,0,0,0,0,'deleted',0,'2026-06-12 10:33:13.469010','2026-06-12 10:34:08.659699',10),(9,'返回格式测试','这是教程内容，使用Markdown格式...','',0,0,0,0,0,0,0,'deleted',0,'2026-06-12 10:38:10.289770','2026-06-12 10:38:10.289796',10),(10,'F2L公式','![F2L-07](/media/formulas/F2L_Images/F2L_007.png)\r\n\r\n# 发文测试，F2L','',35,0,0,0,0,0,0,'deleted',0,'2026-07-25 10:01:52.570561','2026-07-25 12:07:25.090391',10),(11,'111111','![F2L-05](/media/formulas/F2L_Images/F2L_005.png)![F2L-10](/media/formulas/F2L_Images/F2L_010.png)![admin](/media/forum/posts/2026/07/admin.png)![bh01](/media/forum/posts/2026/07/bh01_m3QZaCZ.png)![admin](/media/forum/posts/2026/07/admin_g2v0Okt.png)','',17,0,0,0,0,0,0,'deleted',0,'2026-07-25 10:53:46.442350','2026-07-25 12:07:44.919342',10),(12,'测试多图帖子','![F2L-01](/media/formulas/F2L_Images/F2L_001.png)\n![F2L-02](/media/formulas/F2L_Images/F2L_002.png)\n![F2L-03](/media/formulas/F2L_Images/F2L_003.png)','',1,0,0,0,0,0,0,'deleted',0,'2026-07-25 10:57:30.527408','2026-07-25 10:57:30.527435',10),(13,'111111','![F2L-09](/media/formulas/F2L_Images/F2L_009.png)\r\n![F2L-07](/media/formulas/F2L_Images/F2L_007.png)\r\n![F2L-03](/media/formulas/F2L_Images/F2L_003.png)\r\n![admin_cropped](/media/forum/posts/2026/07/admin_cropped_compressed.webp)','',27,0,0,1,0,0,0,'deleted',0,'2026-07-25 11:00:14.679846','2026-07-25 15:01:42.047184',10),(14,'这是一个标题','**这是一个标题**\r\n![图片](/media/forum/posts/2026/08/image_compressed.webp)','**这是一个标题**\r\n![图片](/media/forum/posts/2026/08/image_compressed.webp)',6,0,0,0,0,0,0,'published',0,'2026-08-18 09:52:53.529089','2026-08-18 09:52:53.529121',17);
/*!40000 ALTER TABLE `forum_post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_post_collect`
--

DROP TABLE IF EXISTS `forum_post_collect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_post_collect` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `forum_post_collect_post_id_user_id_3cbd7f97_uniq` (`post_id`,`user_id`),
  KEY `forum_post_collect_user_id_b2a3c9ad_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `forum_post_collect_post_id_5e799cb7_fk_forum_post_id` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`),
  CONSTRAINT `forum_post_collect_user_id_b2a3c9ad_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_post_collect`
--

LOCK TABLES `forum_post_collect` WRITE;
/*!40000 ALTER TABLE `forum_post_collect` DISABLE KEYS */;
INSERT INTO `forum_post_collect` VALUES (6,'2026-06-07 10:37:12.153830',2,10),(10,'2026-07-25 14:46:08.519848',13,10),(11,'2026-08-18 08:18:15.589309',3,10),(12,'2026-08-18 09:51:40.115423',5,17);
/*!40000 ALTER TABLE `forum_post_collect` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_post_image`
--

DROP TABLE IF EXISTS `forum_post_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_post_image` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `image` varchar(100) NOT NULL,
  `alt` varchar(200) NOT NULL,
  `order` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `forum_post_image_post_id_95977176_fk_forum_post_id` (`post_id`),
  CONSTRAINT `forum_post_image_post_id_95977176_fk_forum_post_id` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_post_image`
--

LOCK TABLES `forum_post_image` WRITE;
/*!40000 ALTER TABLE `forum_post_image` DISABLE KEYS */;
INSERT INTO `forum_post_image` VALUES (2,'formulas/F2L_Images/F2L_007.png','公式缩略图',0,'2026-07-25 10:20:30.594850',10),(3,'forum/posts/2026/07/admin.png','admin_png',0,'2026-07-25 10:54:42.501816',11),(4,'forum/posts/2026/07/bh01_m3QZaCZ.png','bh01_png',0,'2026-07-25 10:55:47.760011',11),(5,'forum/posts/2026/07/admin_g2v0Okt.png','admin_png',0,'2026-07-25 10:56:36.573952',11),(6,'forum/posts/2026/07/admin_gqSlQE7.png','admin_png',0,'2026-07-25 10:57:11.725194',NULL),(7,'formulas/F2L_Images/F2L_001.png','公式缩略图',0,'2026-07-25 10:57:30.550732',12),(8,'formulas/F2L_Images/F2L_002.png','公式缩略图',1,'2026-07-25 10:57:30.569300',12),(9,'formulas/F2L_Images/F2L_003.png','公式缩略图',2,'2026-07-25 10:57:30.589398',12),(11,'formulas/F2L_Images/F2L_003.png','图片',0,'2026-07-25 12:07:12.371794',13),(12,'formulas/F2L_Images/F2L_007.png','图片',0,'2026-07-25 12:07:12.402786',13),(13,'formulas/F2L_Images/F2L_009.png','图片',0,'2026-07-25 12:07:12.424067',13),(14,'formulas/F2L_Images/F2L_005.png','图片',3,'2026-07-25 12:07:44.951916',11),(15,'formulas/F2L_Images/F2L_010.png','图片',3,'2026-07-25 12:07:44.972344',11),(16,'forum/posts/2026/07/admin_cropped_compressed.webp','admin_cropped_webp',0,'2026-07-25 15:01:14.517408',NULL),(17,'forum/posts/2026/07/admin_cropped_compressed.webp','图片',3,'2026-07-25 15:01:42.061366',13),(18,'forum/posts/2026/08/bh01_cropped_compressed.webp','bh01_cropped_webp',0,'2026-08-18 08:06:31.335942',NULL),(19,'forum/posts/2026/08/bh01_cropped_compressed.webp','图片',1,'2026-08-18 08:06:46.907381',4),(20,'forum/posts/2026/08/image_compressed.webp','image_png',0,'2026-08-18 09:52:46.403065',NULL),(21,'forum/posts/2026/08/image_compressed.webp','图片',0,'2026-08-18 09:52:53.540006',14);
/*!40000 ALTER TABLE `forum_post_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_post_like`
--

DROP TABLE IF EXISTS `forum_post_like`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_post_like` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `forum_post_like_post_id_user_id_c7f796d2_uniq` (`post_id`,`user_id`),
  KEY `forum_post_like_user_id_8bb1cc47_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `forum_post_like_post_id_d9d17230_fk_forum_post_id` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`),
  CONSTRAINT `forum_post_like_user_id_8bb1cc47_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_post_like`
--

LOCK TABLES `forum_post_like` WRITE;
/*!40000 ALTER TABLE `forum_post_like` DISABLE KEYS */;
INSERT INTO `forum_post_like` VALUES (8,'2026-06-12 08:17:06.543084',2,10),(11,'2026-07-19 23:28:46.715352',2,1),(12,'2026-07-19 23:28:52.110702',5,1),(13,'2026-07-19 23:28:56.340475',4,1),(14,'2026-07-20 00:17:43.252321',1,1),(16,'2026-08-18 08:16:28.456612',4,10),(18,'2026-08-18 08:19:40.669577',3,10);
/*!40000 ALTER TABLE `forum_post_like` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_post_tags`
--

DROP TABLE IF EXISTS `forum_post_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_post_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `post_id` bigint NOT NULL,
  `tag_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `forum_post_tags_post_id_tag_id_507521d9_uniq` (`post_id`,`tag_id`),
  KEY `forum_post_tags_tag_id_c1772c43_fk_forum_tag_id` (`tag_id`),
  CONSTRAINT `forum_post_tags_post_id_e73359c8_fk_forum_post_id` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`),
  CONSTRAINT `forum_post_tags_tag_id_c1772c43_fk_forum_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `forum_tag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_post_tags`
--

LOCK TABLES `forum_post_tags` WRITE;
/*!40000 ALTER TABLE `forum_post_tags` DISABLE KEYS */;
INSERT INTO `forum_post_tags` VALUES (1,'2026-06-05 09:55:10.815327',1,2),(2,'2026-06-05 09:55:10.815347',1,3),(3,'2026-06-05 09:55:10.833407',2,1),(4,'2026-06-05 09:55:10.833426',2,2),(5,'2026-06-05 09:55:10.849470',3,1),(6,'2026-06-05 09:56:27.085009',4,1),(7,'2026-06-05 09:56:27.085030',4,2),(8,'2026-06-05 09:56:27.085040',4,3),(9,'2026-06-12 10:08:08.870926',5,1),(10,'2026-06-12 10:08:08.870958',5,2),(11,'2026-06-12 10:25:11.489481',6,8),(12,'2026-06-12 10:25:11.489502',6,5),(13,'2026-06-12 10:28:11.728520',7,1),(14,'2026-06-12 10:28:11.728539',7,2),(15,'2026-06-12 10:28:11.728548',7,3),(16,'2026-06-12 10:33:13.497816',8,8),(17,'2026-06-12 10:33:13.497834',8,5),(18,'2026-06-12 10:38:10.303698',9,1),(19,'2026-06-12 10:38:10.303718',9,2),(20,'2026-06-12 10:38:10.303732',9,3),(21,'2026-07-25 10:01:52.595640',10,1),(22,'2026-07-25 10:01:52.595662',10,2),(23,'2026-07-25 10:53:46.468193',11,1),(24,'2026-07-25 10:53:46.468217',11,4),(25,'2026-07-25 11:00:14.691958',13,1),(26,'2026-08-18 09:52:53.534571',14,1),(27,'2026-08-18 09:52:53.534590',14,2);
/*!40000 ALTER TABLE `forum_post_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_report`
--

DROP TABLE IF EXISTS `forum_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_report` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content_type` varchar(20) NOT NULL,
  `object_id` int NOT NULL,
  `reason` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `handled_at` datetime(6) DEFAULT NULL,
  `handler_id` bigint DEFAULT NULL,
  `reporter_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `forum_report_content_type_object_id_reporter_id_93eed8a9_uniq` (`content_type`,`object_id`,`reporter_id`),
  KEY `forum_report_handler_id_2f41d3fd_fk_accounts_user_id` (`handler_id`),
  KEY `forum_report_reporter_id_f7e3028b_fk_accounts_user_id` (`reporter_id`),
  CONSTRAINT `forum_report_handler_id_2f41d3fd_fk_accounts_user_id` FOREIGN KEY (`handler_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `forum_report_reporter_id_f7e3028b_fk_accounts_user_id` FOREIGN KEY (`reporter_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_report`
--

LOCK TABLES `forum_report` WRITE;
/*!40000 ALTER TABLE `forum_report` DISABLE KEYS */;
/*!40000 ALTER TABLE `forum_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forum_tag`
--

DROP TABLE IF EXISTS `forum_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forum_tag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `color` varchar(7) NOT NULL,
  `use_count` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forum_tag`
--

LOCK TABLES `forum_tag` WRITE;
/*!40000 ALTER TABLE `forum_tag` DISABLE KEYS */;
INSERT INTO `forum_tag` VALUES (1,'CFOP','#409EFF',0,'2026-06-05 09:55:05.546802'),(2,'三阶','#67C23A',0,'2026-06-05 09:55:05.564346'),(3,'新手','#E6A23C',0,'2026-06-05 09:55:05.574724'),(4,'进阶','#F56C6C',0,'2026-06-05 09:55:05.583359'),(5,'四阶','#909399',0,'2026-06-05 09:55:05.592045'),(6,'高阶','#9C27B0',0,'2026-06-05 09:55:05.601194'),(7,'二阶','#FF9800',0,'2026-06-05 09:55:05.608486'),(8,'公式','#00BCD4',0,'2026-06-05 09:55:05.621140'),(9,'技巧','#795548',0,'2026-06-05 09:55:05.629283'),(10,'比赛','#FF5722',0,'2026-06-05 09:55:05.636622');
/*!40000 ALTER TABLE `forum_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `home_banner`
--

DROP TABLE IF EXISTS `home_banner`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `home_banner` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) NOT NULL,
  `description` varchar(255) NOT NULL,
  `image` varchar(100) NOT NULL,
  `link` varchar(500) NOT NULL,
  `sort_order` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `home_banner`
--

LOCK TABLES `home_banner` WRITE;
/*!40000 ALTER TABLE `home_banner` DISABLE KEYS */;
INSERT INTO `home_banner` VALUES (1,'魔方入门教程','从零开始学习三阶魔方复原，掌握层先法，轻松入门','banners/banner1.png','/tutorial/beginner',1,1,'2026-07-24 14:14:47.232582'),(2,'CFOP速拧技巧','学习CFOP高级解法，提升复原速度至专业水平','banners/banner2.png','/tutorial/cfop',2,1,'2026-07-24 14:14:47.247469'),(3,'公式库大全','收录数千条魔方公式，支持搜索和收藏，助你突破瓶颈','banners/banner3.png','/formulas',3,1,'2026-07-24 14:14:47.254753');
/*!40000 ALTER TABLE `home_banner` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `home_navigationmenu`
--

DROP TABLE IF EXISTS `home_navigationmenu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `home_navigationmenu` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `index` varchar(20) NOT NULL,
  `label` varchar(50) NOT NULL,
  `path` varchar(250) NOT NULL,
  `category` varchar(20) NOT NULL,
  `sort_order` int NOT NULL,
  `match_paths` json NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `index` (`index`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `home_navigationmenu`
--

LOCK TABLES `home_navigationmenu` WRITE;
/*!40000 ALTER TABLE `home_navigationmenu` DISABLE KEYS */;
INSERT INTO `home_navigationmenu` VALUES (12,'1','首页','/','main',10,'[\"/home\"]'),(13,'2','教程','/tutorials','main',20,'[\"/tutorials\"]'),(14,'3','公式库','/formulas','main',30,'[\"/formulas\"]'),(15,'4','计时器','/timer','main',40,'[\"/timer\"]'),(16,'5','交流论坛','/forum','main',50,'[\"/forum\"]'),(17,'6','魔方商店','/shop','main',60,'[\"/shop\"]'),(18,'p-1','返回首页','/','profile',10,'[]'),(19,'p-2','个人信息','/profiles/info','profile',20,'[\"/profiles/info\"]'),(20,'p-3','公式收藏','/profiles/collections','profile',30,'[\"/profiles/collections\"]'),(21,'p-4','我的数据','/profiles/data','profile',40,'[\"/profiles/data\"]'),(22,'p-5','我的帖子','/profiles/posts','profile',50,'[\"/profiles/posts\"]'),(23,'7','魔友','/users','main',55,'[\"/users\"]');
/*!40000 ALTER TABLE `home_navigationmenu` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_address`
--

DROP TABLE IF EXISTS `shop_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_address` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `province` varchar(50) NOT NULL,
  `city` varchar(50) NOT NULL,
  `district` varchar(50) NOT NULL,
  `detail` varchar(500) NOT NULL,
  `is_default` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_address_user_id_3edd3b17_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `shop_address_user_id_3edd3b17_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_address`
--

LOCK TABLES `shop_address` WRITE;
/*!40000 ALTER TABLE `shop_address` DISABLE KEYS */;
INSERT INTO `shop_address` VALUES (1,'01','13900001111','四川省','成都','郫都区','四川 成都 四川省成都市郫都犀安路999号',1,0,'2026-07-24 16:49:16.534284','2026-07-24 16:49:16.536256',1);
/*!40000 ALTER TABLE `shop_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_cart`
--

DROP TABLE IF EXISTS `shop_cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_cart` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int NOT NULL,
  `selected_spec` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_cart_user_id_27925ac6_fk_accounts_user_id` (`user_id`),
  KEY `shop_cart_product_id_48b482ee_fk_shop_product_id` (`product_id`),
  CONSTRAINT `shop_cart_product_id_48b482ee_fk_shop_product_id` FOREIGN KEY (`product_id`) REFERENCES `shop_product` (`id`),
  CONSTRAINT `shop_cart_user_id_27925ac6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_cart`
--

LOCK TABLES `shop_cart` WRITE;
/*!40000 ALTER TABLE `shop_cart` DISABLE KEYS */;
/*!40000 ALTER TABLE `shop_cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_order`
--

DROP TABLE IF EXISTS `shop_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_order` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_no` varchar(32) NOT NULL,
  `total_amount` decimal(12,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `address` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  `shipped_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_no` (`order_no`),
  KEY `shop_order_user_id_00aba627_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `shop_order_user_id_00aba627_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_order`
--

LOCK TABLES `shop_order` WRITE;
/*!40000 ALTER TABLE `shop_order` DISABLE KEYS */;
INSERT INTO `shop_order` VALUES (1,'ORD202607081622245B62EBFB',204.80,'pending','{\"name\": \"11\", \"phone\": \"11\", \"detail\": \"11111\"}','2026-07-08 16:22:24.160142',NULL,NULL,NULL,1);
/*!40000 ALTER TABLE `shop_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_order_item`
--

DROP TABLE IF EXISTS `shop_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_order_item` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `price` decimal(10,2) NOT NULL,
  `quantity` int NOT NULL,
  `selected_spec` json NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_order_item_order_id_fb1c4e35_fk_shop_order_id` (`order_id`),
  KEY `shop_order_item_product_id_270f6177_fk_shop_product_id` (`product_id`),
  CONSTRAINT `shop_order_item_order_id_fb1c4e35_fk_shop_order_id` FOREIGN KEY (`order_id`) REFERENCES `shop_order` (`id`),
  CONSTRAINT `shop_order_item_product_id_270f6177_fk_shop_product_id` FOREIGN KEY (`product_id`) REFERENCES `shop_product` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_order_item`
--

LOCK TABLES `shop_order_item` WRITE;
/*!40000 ALTER TABLE `shop_order_item` DISABLE KEYS */;
INSERT INTO `shop_order_item` VALUES (1,159.90,1,'{\"颜色\": \"黑色\"}',1,12),(2,44.90,1,'{}',1,8);
/*!40000 ALTER TABLE `shop_order_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_product`
--

DROP TABLE IF EXISTS `shop_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `original_price` decimal(10,2) DEFAULT NULL,
  `stock` int NOT NULL,
  `images` json NOT NULL,
  `thumbnail` varchar(100) DEFAULT NULL,
  `is_on_sale` tinyint(1) NOT NULL,
  `sales_count` int NOT NULL,
  `specs` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `category_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_product_category_id_14d7eea8_fk_shop_product_category_id` (`category_id`),
  CONSTRAINT `shop_product_category_id_14d7eea8_fk_shop_product_category_id` FOREIGN KEY (`category_id`) REFERENCES `shop_product_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_product`
--

LOCK TABLES `shop_product` WRITE;
/*!40000 ALTER TABLE `shop_product` DISABLE KEYS */;
INSERT INTO `shop_product` VALUES (1,'三阶速拧魔方','专业级三阶魔方，顺滑手感，适合速拧练习和比赛',49.90,69.90,100,'[]','products/product_1_6a905cb0_85tRejH.png',1,256,'{\"版本\": [\"标准版\", \"升级版\"], \"颜色\": [\"白色\", \"黑色\"]}','2026-07-08 15:23:43.549763','2026-07-24 12:36:10.974550',1),(2,'三阶磁力魔方','内置磁力定位系统，转体定位精准，提升还原速度',89.90,119.90,80,'[]','products/product_2_846bf74f_JRNoo8V.png',1,134,'{\"颜色\": [\"白色\", \"黑色\"]}','2026-07-08 15:23:43.559222','2026-07-24 12:36:13.703024',1),(3,'三阶初学者套装','适合新手入门的三阶魔方套装，包含教程和配件',29.90,39.90,150,'[]','products/product_3_9e79361c_tBy2pvd.png',1,567,'{\"颜色\": [\"白色\"]}','2026-07-08 15:23:43.568172','2026-07-24 12:36:17.004180',1),(4,'四阶魔方','经典四阶魔方，结构稳定，适合进阶玩家',79.90,99.90,60,'[]','products/product_4_0d3de778_dFZnKAk.png',1,89,'{\"颜色\": [\"白色\", \"黑色\"]}','2026-07-08 15:23:43.575344','2026-07-24 12:36:21.095764',2),(5,'四阶磁力魔方','四阶磁力版本，手感顺滑，定位精准',129.90,159.90,40,'[]','products/product_5_2007a332_NcOYjYD.png',1,56,'{\"颜色\": [\"黑色\"]}','2026-07-08 15:23:43.583150','2026-07-24 12:36:25.256343',2),(6,'五阶魔方','五阶高阶魔方，挑战你的极限',109.90,139.90,50,'[]','products/product_6_d1976c7c_wmXKpYt.png',1,45,'{\"颜色\": [\"白色\", \"黑色\"]}','2026-07-08 15:23:43.590697','2026-07-24 12:36:27.203926',3),(7,'金字塔魔方','经典异形魔方，四面体结构，锻炼空间思维',39.90,49.90,70,'[]','products/product_7_0dc034d4_2Da42c3.png',1,123,'{\"颜色\": [\"白色\", \"黑色\"]}','2026-07-08 15:23:43.598135','2026-07-24 12:36:30.958319',4),(8,'斜转魔方','斜转异形魔方，独特的转动方式，趣味性强',44.90,59.90,64,'[]','products/product_8_de39b2c0_j5Ncxy5.png',1,79,'{\"颜色\": [\"白色\"]}','2026-07-08 15:23:43.605257','2026-07-24 12:36:33.217125',4),(9,'魔方底座','亚克力材质，透明美观，展示你的魔方收藏',15.90,19.90,200,'[]','products/product_9_e1586723_PL7ybRT.png',1,345,'{\"颜色\": [\"透明\", \"黑色\"]}','2026-07-08 15:23:43.613682','2026-07-24 12:36:35.089266',5),(10,'魔方润滑油','专业魔方硅油，提升顺滑度，延长魔方寿命',12.90,16.90,180,'[]','products/product_10_93196cdd_i2JHjdE.png',1,289,'{\"规格\": [\"10ml\", \"30ml\"]}','2026-07-08 15:23:43.622100','2026-07-24 12:36:37.993388',5),(11,'魔方贴纸套装','高品质PVC贴纸，多种配色可选，更换方便',9.90,12.90,120,'[]','products/product_11_37982974_z2RPaLL.png',1,178,'{\"类型\": [\"三阶\", \"四阶\", \"五阶\"]}','2026-07-08 15:23:43.629648','2026-07-24 12:36:40.538033',5),(12,'比赛专用魔方','WCA认证比赛用魔方，极致性能，专为竞技设计',159.90,199.90,29,'[]','products/product_12_17af95aa_rJLqvJR.png',1,24,'{\"颜色\": [\"黑色\"]}','2026-07-08 15:23:43.637838','2026-07-24 12:36:42.586243',6);
/*!40000 ALTER TABLE `shop_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shop_product_category`
--

DROP TABLE IF EXISTS `shop_product_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shop_product_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `icon` varchar(100) NOT NULL,
  `sort_order` int NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_product_categor_parent_id_545fc4e9_fk_shop_prod` (`parent_id`),
  CONSTRAINT `shop_product_categor_parent_id_545fc4e9_fk_shop_prod` FOREIGN KEY (`parent_id`) REFERENCES `shop_product_category` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shop_product_category`
--

LOCK TABLES `shop_product_category` WRITE;
/*!40000 ALTER TABLE `shop_product_category` DISABLE KEYS */;
INSERT INTO `shop_product_category` VALUES (1,'三阶魔方','',1,'','2026-07-08 15:23:43.455558',NULL),(2,'四阶魔方','',2,'','2026-07-08 15:23:43.470730',NULL),(3,'五阶及以上','',3,'','2026-07-08 15:23:43.478856',NULL),(4,'异形魔方','',4,'','2026-07-08 15:23:43.486117',NULL),(5,'魔方配件','',5,'','2026-07-08 15:23:43.493028',NULL),(6,'比赛专用','',6,'','2026-07-08 15:23:43.500671',NULL);
/*!40000 ALTER TABLE `shop_product_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `timer_record`
--

DROP TABLE IF EXISTS `timer_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `timer_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cube_type` varchar(10) NOT NULL,
  `method` varchar(20) NOT NULL,
  `time_ms` int NOT NULL,
  `scramble` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `timer_record_user_id_eedfa320_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `timer_record_user_id_eedfa320_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `timer_record`
--

LOCK TABLES `timer_record` WRITE;
/*!40000 ALTER TABLE `timer_record` DISABLE KEYS */;
INSERT INTO `timer_record` VALUES (3,'3x3','cfop',19541,'U\' F2 L2 D B\' U\' B R\' B D\' L D2 L\' B2 L\' U\' F\' R\' F\' D2 R\'','2026-07-19 20:04:39.390944',1),(6,'3x3','cfop',931,'B U2 B U D B L F U2 L\' B R\' U D\' B R\' B2 D\' L\' B\' D\'','2026-08-17 11:15:03.411426',17),(7,'3x3','cfop',1819,'F L\' D\' U2 L U\' B2 F\' R2 D2 R F L\' R\' U L2 B2 U B L2 U\'','2026-08-17 11:15:08.862753',17),(8,'3x3','cfop',3553,'D2 R L R\' B2 R2 U\' B\' D2 U\' B\' F B R\' B\' D F2 B D2 U B','2026-08-17 12:03:42.388427',17),(17,'3x3','cfop',21527,'U\' D\' L\' F2 D\' L D R D\' R U\' R2 B\' D F\' B\' F R\' D2 B U2','2026-08-18 07:27:09.026084',10),(18,'3x3','cfop',29056,'L\' U\' R\' U\' B2 U\' L U\' B\' D2 F2 B\' D\' B2 R\' B\' L F L\' R D\'','2026-08-18 07:53:46.274048',10),(19,'3x3','cfop',20345,'R U\' R2 F\' D B2 U2 F2 U R2 U\' F\' D\' U2 D2 B D2 U L2 U R\'','2026-08-18 11:21:24.550240',10);
/*!40000 ALTER TABLE `timer_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'icube_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-19 10:11:57
