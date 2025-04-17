-- MySQL dump 10.13  Distrib 8.0.39, for Win64 (x86_64)
--
-- Host: localhost    Database: miaoyun_db
-- ------------------------------------------------------
-- Server version	8.0.39

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
-- Table structure for table `attendance_attendancerecord`
--

DROP TABLE IF EXISTS `attendance_attendancerecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_attendancerecord` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `check_in_time` datetime(6) NOT NULL,
  `check_out_time` datetime(6) DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration` double DEFAULT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `piano_id` bigint DEFAULT NULL,
  `session_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  `check_in_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration_minutes` double DEFAULT NULL,
  `note` longtext COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (_utf8mb3''),
  PRIMARY KEY (`id`),
  UNIQUE KEY `attendance_attendancerecord_session_id_student_id_7a8c3d0e_uniq` (`session_id`,`student_id`),
  KEY `attendance_attendanc_piano_id_b9917673_fk_courses_p` (`piano_id`),
  KEY `attendance_attendanc_student_id_d242c468_fk_students_` (`student_id`),
  CONSTRAINT `attendance_attendanc_piano_id_b9917673_fk_courses_p` FOREIGN KEY (`piano_id`) REFERENCES `courses_piano` (`id`),
  CONSTRAINT `attendance_attendanc_session_id_ddf44875_fk_attendanc` FOREIGN KEY (`session_id`) REFERENCES `attendance_attendancesession` (`id`),
  CONSTRAINT `attendance_attendanc_student_id_d242c468_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance_attendancerecord`
--

LOCK TABLES `attendance_attendancerecord` WRITE;
/*!40000 ALTER TABLE `attendance_attendancerecord` DISABLE KEYS */;
INSERT INTO `attendance_attendancerecord` VALUES (1,'2025-04-02 11:26:57.432744','2025-04-02 04:27:35.548255','checked_out',138578427,'',1,8,1,'qrcode',NULL,''),(2,'2025-04-02 11:26:57.432744','2025-04-02 10:45:44.527613','checked_out',0.05140847,'',NULL,11,2,'manual',3.0845082,''),(3,'2025-04-02 11:26:57.432744','2025-04-02 10:45:40.005237','checked_out',0.03686732888888889,'',NULL,11,1,'manual',2.2120397333333335,''),(6,'2025-04-04 17:48:38.566424','2025-04-05 04:13:37.353262','checked_out',10.416329677222222,'',NULL,14,1,'qrcode',624.9797806333333,''),(7,'2025-04-05 10:17:30.538933','2025-04-05 13:40:26.546684','checked_out',3.3822243752777776,'',1,17,1,'qrcode',202.93346251666665,''),(8,'2025-04-06 07:47:07.153897','2025-04-06 19:02:46.856839','checked_out',11.261028595,'',1,18,2,'qrcode',675.6617157000001,''),(9,'2025-04-06 12:54:11.277216','2025-04-07 04:09:35.274429','checked_out',15.256665892500001,'',NULL,18,3,'qrcode',915.3999535500001,''),(10,'2025-04-07 06:49:44.527452','2025-04-07 07:19:00.000000','checked_out',0.5,'',1,22,3,'qrcode',30,''),(11,'2025-04-07 06:54:02.061219','2025-04-07 07:23:00.000000','checked_out',0.5,'',1,21,1,'qrcode',30,''),(12,'2025-04-07 07:11:04.481947','2025-04-07 07:41:04.476442','checked_out',0.5,'',1,22,2,'qrcode',30,''),(13,'2025-04-07 07:13:50.721501','2025-04-07 07:43:50.721501','checked_out',0.5,'',1,22,1,'qrcode',30,''),(14,'2025-04-07 07:17:37.526855','2025-04-07 07:47:37.526855','checked_out',0.5,'',1,21,3,'qrcode',30,''),(15,'2025-04-07 07:20:06.422762','2025-04-07 07:50:06.422762','checked_out',0.5,'',1,21,2,'qrcode',30,''),(16,'2025-04-07 07:21:19.158697','2025-04-07 07:51:19.158697','checked_out',0.5,'',1,20,3,'qrcode',30,''),(17,'2025-04-07 07:55:52.759932','2025-04-07 12:56:40.076097','checked_out',5.013143379166666,'',2,23,1,'qrcode',300.78860275,''),(18,'2025-04-07 08:45:09.798860','2025-04-07 12:56:40.056383','checked_out',4.191738200833333,'',2,23,2,'qrcode',251.50429204999998,''),(19,'2025-04-07 13:02:22.639205','2025-04-08 04:08:53.236626','checked_out',15.10849928361111,'',2,23,3,'qrcode',906.5099570166666,''),(20,'2025-04-08 06:04:25.883653','2025-04-08 11:46:57.508686','checked_out',5.708784731388889,'',1,26,1,'qrcode',342.5270838833333,''),(21,'2025-04-08 06:40:04.911962','2025-04-08 11:46:57.492743','checked_out',5.1146057725,'',2,26,2,'qrcode',306.87634635,''),(22,'2025-04-08 11:57:18.293303','2025-04-08 13:15:10.774631','checked_out',1.2833333333333334,'',1,27,1,'qrcode',77,''),(23,'2025-04-08 15:32:02.517161','2025-04-09 05:56:07.792611','checked_out',14.401465402777777,'',1,27,2,'qrcode',864.0879241666667,''),(24,'2025-04-08 15:34:49.823928','2025-04-09 05:56:07.777441','checked_out',14.354987086944444,'',2,27,3,'qrcode',861.2992252166666,''),(25,'2025-04-09 14:37:21.891811','2025-04-09 15:44:36.171285','checked_out',1.1166666666666667,'',1,28,1,'qrcode',67,''),(26,'2025-04-09 14:37:49.834792','2025-04-09 15:49:58.466416','checked_out',1.2023976733333333,'',2,28,2,'qrcode',72.1438604,'');
/*!40000 ALTER TABLE `attendance_attendancerecord` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attendance_attendancesession`
--

DROP TABLE IF EXISTS `attendance_attendancesession`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_attendancesession` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `start_time` datetime(6) NOT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_id` bigint DEFAULT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `qrcode_id` bigint DEFAULT NULL,
  `schedule_id` bigint DEFAULT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (_utf8mb3''),
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `qrcode_id` (`qrcode_id`),
  KEY `attendance_attendanc_created_by_id_8831185e_fk_users_use` (`created_by_id`),
  KEY `attendance_attendanc_course_id_12986a31_fk_courses_c` (`course_id`),
  KEY `attendance_attendanc_schedule_id_5ade9e14_fk_courses_c` (`schedule_id`),
  CONSTRAINT `attendance_attendanc_course_id_12986a31_fk_courses_c` FOREIGN KEY (`course_id`) REFERENCES `courses_course` (`id`),
  CONSTRAINT `attendance_attendanc_created_by_id_8831185e_fk_users_use` FOREIGN KEY (`created_by_id`) REFERENCES `users_user` (`id`),
  CONSTRAINT `attendance_attendanc_qrcode_id_1b87e839_fk_attendanc` FOREIGN KEY (`qrcode_id`) REFERENCES `attendance_qrcode` (`id`),
  CONSTRAINT `attendance_attendanc_schedule_id_5ade9e14_fk_courses_c` FOREIGN KEY (`schedule_id`) REFERENCES `courses_courseschedule` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance_attendancesession`
--

LOCK TABLES `attendance_attendancesession` WRITE;
/*!40000 ALTER TABLE `attendance_attendancesession` DISABLE KEYS */;
INSERT INTO `attendance_attendancesession` VALUES (1,'2025-04-01 18:02:12.072781','2025-04-04 15:09:15.636033','closed',1,2,4,1,'自动生成的考勤 - 2025-04-01 18:02',0),(2,'2025-04-01 18:02:32.545657','2025-04-04 15:09:15.633962','closed',1,2,5,1,'自动生成的考勤 - 2025-04-01 18:02',0),(3,'2025-04-01 18:04:02.293917','2025-04-04 15:09:15.631858','closed',1,2,6,1,'自动生成的考勤 - 2025-04-01 18:04',0),(4,'2025-04-01 18:04:06.026330','2025-04-04 15:09:15.629498','closed',1,2,7,1,'自动生成的考勤 - 2025-04-01 18:04',0),(5,'2025-04-01 18:04:08.516379','2025-04-04 15:09:15.627388','closed',1,2,8,1,'自动生成的考勤 - 2025-04-01 18:04',0),(6,'2025-04-01 18:04:10.580714','2025-04-04 15:09:15.625311','closed',1,2,9,1,'自动生成的考勤 - 2025-04-01 18:04',0),(7,'2025-04-02 02:08:43.024419','2025-04-04 15:09:15.623287','closed',1,2,10,2,'自动生成的考勤 - 2025-04-02 02:08',0),(8,'2025-04-02 02:17:22.217102','2025-04-04 15:09:15.620782','closed',1,2,11,2,'自动生成的考勤 - 2025-04-02 02:17',0),(9,'2025-04-02 10:02:00.740988','2025-04-04 15:09:15.618358','closed',1,2,12,2,'自动生成的考勤 - 2025-04-02 10:02',0),(10,'2025-04-02 10:34:40.244414','2025-04-04 15:09:15.616083','closed',1,2,13,2,'自动生成的考勤 - 2025-04-02 10:34',0),(11,'2025-04-02 10:35:08.945024','2025-04-04 15:09:15.611205','closed',1,2,14,2,'自动生成的考勤 - 2025-04-02 10:35',0),(14,'2025-04-04 16:27:15.316237','2025-04-05 16:27:15.302509','closed',1,2,60,3,'生成于 2025-04-04 16:27',0),(15,'2025-04-05 06:34:47.787882','2025-04-05 06:47:01.917581','closed',1,2,61,4,'生成于 2025-04-05 06:34',0),(16,'2025-04-05 06:47:10.909729','2025-04-06 06:47:10.885789','closed',1,2,62,5,'生成于 2025-04-05 06:47',0),(17,'2025-04-05 07:17:03.310255','2025-04-06 07:17:03.287607','closed',1,2,63,6,'生成于 2025-04-05 07:17',0),(18,'2025-04-06 07:41:33.738564','2025-04-06 19:05:48.821409','closed',1,2,NULL,7,'生成于 2025-04-06 07:41',0),(19,'2025-04-06 11:05:09.471597','2025-04-06 12:05:09.471597','closed',1,2,NULL,8,'生成于 2025-04-06 19:05',0),(20,'2025-04-06 12:05:16.887432','2025-04-06 15:59:59.859831','closed',1,2,66,9,'生成于 2025-04-06 20:05',0),(21,'2025-04-07 04:29:54.520452','2025-04-07 06:50:53.802279','closed',1,2,NULL,10,'生成于 2025-04-07 12:29',0),(22,'2025-04-07 06:49:44.527452','2025-04-07 07:19:25.205326','closed',1,2,NULL,10,'手动添加的考勤 - 2025-04-07 14:49',0),(23,'2025-04-07 07:27:47.631339','2025-04-07 15:59:59.584938','closed',1,2,68,11,'生成于 2025-04-07 15:27',0),(24,'2025-04-08 04:15:03.982274','2025-04-08 04:46:30.231414','closed',1,2,NULL,12,'生成于 2025-04-08 12:15',0),(25,'2025-04-08 04:46:49.575535','2025-04-08 05:16:42.589531','closed',1,2,70,13,'生成于 2025-04-08 12:46',0),(26,'2025-04-08 05:16:48.309984','2025-04-08 11:49:56.147715','closed',1,2,71,14,'生成于 2025-04-08 13:16',0),(27,'2025-04-08 11:50:11.200656','2025-04-08 15:59:59.166919','closed',1,2,72,15,'生成于 2025-04-08 19:50',0),(28,'2025-04-09 05:58:11.416842','2025-04-09 15:59:59.383276','closed',1,2,73,16,'生成于 2025-04-09 13:58',0);
/*!40000 ALTER TABLE `attendance_attendancesession` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attendance_pianoassignment`
--

DROP TABLE IF EXISTS `attendance_pianoassignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_pianoassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reserved_time` datetime(6) NOT NULL,
  `expiration_time` datetime(6) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `piano_id` bigint NOT NULL,
  `session_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `attendance_pianoassignment_piano_id_545aded8_fk_courses_piano_id` (`piano_id`),
  KEY `attendance_pianoassi_session_id_54c6c675_fk_attendanc` (`session_id`),
  KEY `attendance_pianoassi_student_id_56258343_fk_students_` (`student_id`),
  CONSTRAINT `attendance_pianoassi_session_id_54c6c675_fk_attendanc` FOREIGN KEY (`session_id`) REFERENCES `attendance_attendancesession` (`id`),
  CONSTRAINT `attendance_pianoassi_student_id_56258343_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`),
  CONSTRAINT `attendance_pianoassignment_piano_id_545aded8_fk_courses_piano_id` FOREIGN KEY (`piano_id`) REFERENCES `courses_piano` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance_pianoassignment`
--

LOCK TABLES `attendance_pianoassignment` WRITE;
/*!40000 ALTER TABLE `attendance_pianoassignment` DISABLE KEYS */;
INSERT INTO `attendance_pianoassignment` VALUES (1,'2025-04-07 07:39:22.350346','2025-04-07 07:41:22.349343','expired',1,23,1),(2,'2025-04-07 07:42:41.611933','2025-04-07 07:44:41.611933','expired',1,23,1),(3,'2025-04-07 07:46:47.546674','2025-04-07 07:48:47.545674','expired',1,23,1),(4,'2025-04-07 07:50:05.795695','2025-04-07 07:52:05.795695','expired',1,23,1),(5,'2025-04-07 07:55:49.676359','2025-04-07 07:57:49.676359','expired',1,23,1),(6,'2025-04-07 08:32:17.287051','2025-04-07 08:34:17.287051','expired',1,23,1),(7,'2025-04-07 08:34:25.975752','2025-04-07 08:36:25.975752','expired',1,23,2),(8,'2025-04-07 08:38:14.753897','2025-04-07 08:40:14.753897','expired',1,23,2),(9,'2025-04-07 08:45:06.766607','2025-04-07 08:47:06.766607','expired',1,23,2),(10,'2025-04-07 08:56:18.345129','2025-04-07 08:58:18.345129','expired',1,23,3),(11,'2025-04-07 08:58:47.546449','2025-04-07 09:00:47.546449','expired',1,23,3),(12,'2025-04-07 09:02:56.525381','2025-04-07 09:04:56.525381','expired',1,23,3),(13,'2025-04-07 09:20:13.782936','2025-04-07 09:22:13.782936','expired',1,23,3),(14,'2025-04-07 11:39:03.585481','2025-04-07 11:41:03.585481','expired',1,23,3),(15,'2025-04-07 11:42:52.238000','2025-04-07 11:44:52.238000','expired',1,23,3),(16,'2025-04-07 11:53:44.503807','2025-04-07 11:55:44.503060','expired',1,23,3),(17,'2025-04-07 12:01:20.080370','2025-04-07 12:03:20.079347','expired',1,23,3),(18,'2025-04-07 12:14:05.966532','2025-04-07 12:16:05.966532','expired',1,23,3),(19,'2025-04-07 12:19:42.110371','2025-04-07 12:21:42.110371','expired',1,23,3),(20,'2025-04-07 12:36:25.233185','2025-04-07 12:38:25.233185','expired',1,23,3),(21,'2025-04-07 12:42:49.894102','2025-04-07 12:44:49.894102','expired',1,23,3),(22,'2025-04-07 12:54:54.079874','2025-04-07 12:56:54.079874','expired',1,23,3),(23,'2025-04-07 13:02:20.055410','2025-04-07 13:04:20.055410','expired',1,23,3),(24,'2025-04-08 11:46:57.504267','2025-04-08 11:47:27.504267','expired',2,26,3),(25,'2025-04-08 13:15:56.746374','2025-04-08 13:16:26.745346','assigned',1,27,3),(26,'2025-04-09 14:31:13.160016','2025-04-09 14:31:43.160016','expired',1,28,3),(27,'2025-04-09 15:48:50.816991','2025-04-09 15:49:20.816991','expired',1,28,3);
/*!40000 ALTER TABLE `attendance_pianoassignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attendance_qrcode`
--

DROP TABLE IF EXISTS `attendance_qrcode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_qrcode` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `uuid` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `qr_code_image` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `course_id` bigint NOT NULL,
  `code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `attendance_qrcode_course_id_35a27add_fk_courses_course_id` (`course_id`),
  CONSTRAINT `attendance_qrcode_course_id_35a27add_fk_courses_course_id` FOREIGN KEY (`course_id`) REFERENCES `courses_course` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance_qrcode`
--

LOCK TABLES `attendance_qrcode` WRITE;
/*!40000 ALTER TABLE `attendance_qrcode` DISABLE KEYS */;
INSERT INTO `attendance_qrcode` VALUES (1,'a1a6b277ef504e3f9a64809610309996','2025-04-01 17:57:57.797690','2025-04-01 19:57:57.784839','qrcodes/DEFAULT_202504011757.png',1,'a1a6b277-ef50-4e3f-9a64-809610309996'),(2,'7cdb16ec604b4898bd66e62dff199249','2025-04-01 17:57:57.839757','2025-04-01 19:57:57.822041','qrcodes/DEFAULT_202504011757_eQihI9k.png',1,'7cdb16ec-604b-4898-bd66-e62dff199249'),(3,'24d485ba5f3a4b12b2be8efee112a9d8','2025-04-01 17:57:57.889703','2025-04-01 19:57:57.878960','qrcodes/DEFAULT_202504011757_hLVqYBt.png',1,'24d485ba-5f3a-4b12-b2be-8efee112a9d8'),(4,'e9b1bf6beed3443d9e830eb99ebff034','2025-04-01 18:02:12.068778','2025-04-01 20:02:12.043940','qrcodes/DEFAULT_202504011802.png',1,'e9b1bf6b-eed3-443d-9e83-0eb99ebff034'),(5,'498c5ef6f9334e699fd3ae4d17db7449','2025-04-01 18:02:32.542098','2025-04-01 20:02:32.532588','qrcodes/DEFAULT_202504011802_MMInbvP.png',1,'498c5ef6-f933-4e69-9fd3-ae4d17db7449'),(6,'19e916b121824308a539d77ecb17553e','2025-04-01 18:04:02.290916','2025-04-01 20:04:02.282391','qrcodes/DEFAULT_202504011804.png',1,'19e916b1-2182-4308-a539-d77ecb17553e'),(7,'e833db573c424857b9b6706d00d003df','2025-04-01 18:04:06.023448','2025-04-01 20:04:06.015930','qrcodes/DEFAULT_202504011804_j6EAVu5.png',1,'e833db57-3c42-4857-b9b6-706d00d003df'),(8,'dbd8309f40f94fa780fc816827e0f299','2025-04-01 18:04:08.514379','2025-04-01 20:04:08.506863','qrcodes/DEFAULT_202504011804_wJ6WeGz.png',1,'dbd8309f-40f9-4fa7-80fc-816827e0f299'),(9,'b04f1642bfd74ca4be7bb151996d073d','2025-04-01 18:04:10.576715','2025-04-01 20:04:10.567151','qrcodes/DEFAULT_202504011804_JRn6rJN.png',1,'b04f1642-bfd7-4ca4-be7b-b151996d073d'),(10,'faa7b506cdb3454183e49c8c13363c10','2025-04-02 02:08:43.024419','2025-04-02 04:08:43.000745','qrcodes/DEFAULT_202504020208.png',1,'faa7b506-cdb3-4541-83e4-9c8c13363c10'),(11,'ed3483e6a82f4701b14c33d869d96cf5','2025-04-02 02:17:22.217102','2025-04-03 02:17:22.201105','qrcodes/DEFAULT_202504020217.png',1,'ed3483e6-a82f-4701-b14c-33d869d96cf5'),(12,'2dbfcdd4854044698803d5b8eb948870','2025-04-02 10:02:00.739511','2025-04-03 10:02:00.677596','qrcodes/DEFAULT_202504021002.png',1,'2dbfcdd4-8540-4469-8803-d5b8eb948870'),(13,'8003930c317a45cabdee91558a718ac3','2025-04-02 10:34:40.241000','2025-04-03 10:34:40.223806','qrcodes/DEFAULT_202504021034.png',1,'8003930c-317a-45ca-bdee-91558a718ac3'),(14,'4f8727e30f8d4b0586ea5505086c07ec','2025-04-02 10:35:08.941005','2025-04-03 10:35:08.931505','qrcodes/DEFAULT_202504021035.png',1,'4f8727e3-0f8d-4b05-86ea-5505086c07ec'),(15,'35e0bca3784247cca31741aa7e74b81c','2025-04-04 07:01:07.605351','2025-04-05 07:01:07.581833','qrcodes/DEFAULT_202504040701.png',1,'35e0bca3-7842-47cc-a317-41aa7e74b81c'),(16,'4288cbec8da742d6a0855c6d053e415a','2025-04-04 07:36:10.669100','2025-04-05 07:36:10.651335','qrcodes/DEFAULT_202504040736.png',1,'4288cbec-8da7-42d6-a085-5c6d053e415a'),(17,'5cb8a30a01644caa9864a3989779e272','2025-04-04 07:37:04.246977','2025-04-05 07:37:04.238754','qrcodes/DEFAULT_202504040737.png',1,'5cb8a30a-0164-4caa-9864-a3989779e272'),(18,'d6181845d0b941789fde0efe4f8dcb5a','2025-04-04 07:37:07.577435','2025-04-05 07:37:07.569389','qrcodes/DEFAULT_202504040737_ATljLhU.png',1,'d6181845-d0b9-4178-9fde-0efe4f8dcb5a'),(19,'9cbe85b4b0a74ea09e41574f5ca9a8d2','2025-04-04 07:39:33.847031','2025-04-05 07:39:33.839911','qrcodes/DEFAULT_202504040739.png',1,'9cbe85b4-b0a7-4ea0-9e41-574f5ca9a8d2'),(20,'0cf9d4023804433c897c275f1d990a27','2025-04-04 07:53:20.348205','2025-04-05 07:53:20.324656','qrcodes/DEFAULT_202504040753.png',1,'0cf9d402-3804-433c-897c-275f1d990a27'),(21,'2a5890906b504953bb430afd15ae4b07','2025-04-04 07:53:24.280941','2025-04-05 07:53:24.272848','qrcodes/DEFAULT_202504040753_ArVQMVm.png',1,'2a589090-6b50-4953-bb43-0afd15ae4b07'),(22,'2c9b578e7e154e718fb9bb10717bc2d4','2025-04-04 07:53:24.899485','2025-04-05 07:53:24.891981','qrcodes/DEFAULT_202504040753_V7ZOjPO.png',1,'2c9b578e-7e15-4e71-8fb9-bb10717bc2d4'),(23,'61a90b216c9f42e1b3b95db32ad64971','2025-04-04 07:53:25.446981','2025-04-05 07:53:25.439428','qrcodes/DEFAULT_202504040753_J6u4zX3.png',1,'61a90b21-6c9f-42e1-b3b9-5db32ad64971'),(24,'f1295c6fd375450d92bfa96d49fcf72d','2025-04-04 07:54:02.528729','2025-04-05 07:54:02.521165','qrcodes/DEFAULT_202504040754.png',1,'f1295c6f-d375-450d-92bf-a96d49fcf72d'),(25,'aaf0a8afc3e94272a44217802f2283a1','2025-04-04 07:54:02.547392','2025-04-05 07:54:02.539800','qrcodes/DEFAULT_202504040754_WVGcC5c.png',1,'aaf0a8af-c3e9-4272-a442-17802f2283a1'),(26,'863b4c3ee3574d989f7567b5271f1618','2025-04-04 07:54:02.627875','2025-04-05 07:54:02.620187','qrcodes/DEFAULT_202504040754_nEZpgpI.png',1,'863b4c3e-e357-4d98-9f75-67b5271f1618'),(27,'3f894a20a54c48c7b6514680870c24b6','2025-04-04 07:54:14.059943','2025-04-05 07:54:14.051566','qrcodes/DEFAULT_202504040754_i8beeRk.png',1,'3f894a20-a54c-48c7-b651-4680870c24b6'),(28,'759e5b8109e143b289b26d262b0c8577','2025-04-04 09:23:54.397933','2025-04-05 09:23:54.378510','qrcodes/DEFAULT_202504040923.png',1,'759e5b81-09e1-43b2-89b2-6d262b0c8577'),(29,'5c9921172c824c4da46215eb19e3056e','2025-04-04 09:24:44.854278','2025-04-05 09:24:44.832428','qrcodes/DEFAULT_202504040924.png',1,'5c992117-2c82-4c4d-a462-15eb19e3056e'),(30,'c0b5e26924b8426eab72f57134c42d73','2025-04-04 09:24:44.886147','2025-04-05 09:24:44.875282','qrcodes/DEFAULT_202504040924_THLnGSl.png',1,'c0b5e269-24b8-426e-ab72-f57134c42d73'),(31,'a121b4d8c94c407b984641b272a2e557','2025-04-04 09:25:24.933821','2025-04-05 09:25:24.924161','qrcodes/DEFAULT_202504040925.png',1,'a121b4d8-c94c-407b-9846-41b272a2e557'),(32,'12f98cf56ef84b2488bab06c38159576','2025-04-04 09:26:35.035026','2025-04-05 09:26:35.025491','qrcodes/DEFAULT_202504040926.png',1,'12f98cf5-6ef8-4b24-88ba-b06c38159576'),(33,'bab8e75ca52142bb903c29ef842becb3','2025-04-04 11:03:19.438471','2025-04-05 11:03:19.421165','qrcodes/DEFAULT_202504041103.png',1,'bab8e75c-a521-42bb-903c-29ef842becb3'),(34,'daacd4fb44854fe1a559e0c815b62cc0','2025-04-04 11:30:53.925799','2025-04-05 11:30:53.907952','qrcodes/DEFAULT_202504041130.png',1,'daacd4fb-4485-4fe1-a559-e0c815b62cc0'),(35,'9e52c8c95ed743c48dbc52a69e33b94a','2025-04-04 11:33:38.359582','2025-04-05 11:33:38.350563','qrcodes/DEFAULT_202504041133.png',1,'9e52c8c9-5ed7-43c4-8dbc-52a69e33b94a'),(36,'19e871e0c9354e139757f160abcbc3d8','2025-04-04 11:56:40.969066','2025-04-05 11:56:40.961450','qrcodes/DEFAULT_202504041156.png',1,'19e871e0-c935-4e13-9757-f160abcbc3d8'),(37,'d2be660cb7ed4b619ba9e814a4b6e07c','2025-04-04 13:28:51.966737','2025-04-05 13:28:51.942100','qrcodes/DEFAULT_202504041328.png',1,'d2be660c-b7ed-4b61-9ba9-e814a4b6e07c'),(38,'a0b5dd74639347678dec8db07fc5b836','2025-04-04 13:30:40.415674','2025-04-05 13:30:40.408238','qrcodes/DEFAULT_202504041330.png',1,'a0b5dd74-6393-4767-8dec-8db07fc5b836'),(39,'875991536329485ba3c421aa58419840','2025-04-04 13:39:19.290961','2025-04-05 13:39:19.282787','qrcodes/DEFAULT_202504041339.png',1,'87599153-6329-485b-a3c4-21aa58419840'),(40,'50fee42097e64328bd3528f534e7c4cf','2025-04-04 13:39:23.590705','2025-04-05 13:39:23.582160','qrcodes/DEFAULT_202504041339_us0pw3v.png',1,'50fee420-97e6-4328-bd35-28f534e7c4cf'),(41,'d55f7aed3d8846039717f715dce91e1b','2025-04-04 13:39:23.611920','2025-04-05 13:39:23.602127','qrcodes/DEFAULT_202504041339_weXyXzy.png',1,'d55f7aed-3d88-4603-9717-f715dce91e1b'),(42,'354964bf83944893a921278f33226a86','2025-04-04 13:39:23.701070','2025-04-05 13:39:23.690524','qrcodes/DEFAULT_202504041339_eOE6Tcv.png',1,'354964bf-8394-4893-a921-278f33226a86'),(43,'b1a1a92302574a9fa6e248adf41a1b7b','2025-04-04 13:52:44.928484','2025-04-05 13:52:44.919900','qrcodes/DEFAULT_202504041352.png',1,'b1a1a923-0257-4a9f-a6e2-48adf41a1b7b'),(44,'adca705b27424714b7cf307ec87c3932','2025-04-04 14:01:24.916724','2025-04-05 14:01:24.897621','qrcodes/DEFAULT_202504041401.png',1,'adca705b-2742-4714-b7cf-307ec87c3932'),(45,'5dc443dc64da4c04bebd54ab0712c6b1','2025-04-04 14:06:41.707999','2025-04-05 14:06:41.697108','qrcodes/DEFAULT_202504041406.png',1,'5dc443dc-64da-4c04-bebd-54ab0712c6b1'),(46,'5c24fb448c97424e8974580574efbd6c','2025-04-04 14:06:44.900565','2025-04-05 14:06:44.893039','qrcodes/DEFAULT_202504041406_JZDp6ri.png',1,'5c24fb44-8c97-424e-8974-580574efbd6c'),(47,'98c63bc7f3f34330ab36adb650cbdf42','2025-04-04 14:06:44.927298','2025-04-05 14:06:44.916803','qrcodes/DEFAULT_202504041406_2KpF8bP.png',1,'98c63bc7-f3f3-4330-ab36-adb650cbdf42'),(48,'819b7aa50c6b4d49863590183fe55aa7','2025-04-04 14:06:45.008464','2025-04-05 14:06:44.998041','qrcodes/DEFAULT_202504041406_VAJOS1L.png',1,'819b7aa5-0c6b-4d49-8635-90183fe55aa7'),(49,'b6cefd5b6fc9432d805d8a484e1215ef','2025-04-04 14:12:28.004715','2025-04-05 14:12:27.983628','qrcodes/DEFAULT_202504041412.png',1,'b6cefd5b-6fc9-432d-805d-8a484e1215ef'),(50,'c7b551723808426c9ad0cad50bda5ec4','2025-04-04 14:13:52.733947','2025-04-05 14:13:52.717439','qrcodes/DEFAULT_202504041413.png',1,'c7b55172-3808-426c-9ad0-cad50bda5ec4'),(51,'707248925fce49a3b52a1733df8c4ef0','2025-04-04 14:13:53.856335','2025-04-05 14:13:53.846280','qrcodes/DEFAULT_202504041413_w0Zso6V.png',1,'70724892-5fce-49a3-b52a-1733df8c4ef0'),(52,'3f071f4429454eecacff248baea1ca93','2025-04-04 14:15:23.158583','2025-04-05 14:15:23.150077','qrcodes/DEFAULT_202504041415.png',1,'3f071f44-2945-4eec-acff-248baea1ca93'),(53,'6d8dbad9a32e4e1ebddd5a4b752011f9','2025-04-04 14:39:19.968440','2025-04-05 14:39:19.951294','qrcodes/DEFAULT_202504041439.png',1,'6d8dbad9-a32e-4e1e-bddd-5a4b752011f9'),(54,'b41fabcabab644e3a5540f9cb7636ee9','2025-04-04 14:39:36.076739','2025-04-05 14:39:36.069118','qrcodes/DEFAULT_202504041439_NCZD6vp.png',1,'b41fabca-bab6-44e3-a554-0f9cb7636ee9'),(55,'01d5af57d8074509887db867432c8b99','2025-04-04 14:39:38.280673','2025-04-05 14:39:38.272671','qrcodes/DEFAULT_202504041439_40IQ50r.png',1,'01d5af57-d807-4509-887d-b867432c8b99'),(56,'9582043e0366479f89d1a57c71dd8d86','2025-04-04 15:13:31.752011','2025-04-05 15:13:31.733893','qrcodes/DEFAULT_202504041513.png',1,'9582043e-0366-479f-89d1-a57c71dd8d86'),(57,'f29548361bd34885aa874e97d274c1e8','2025-04-04 15:54:50.815888','2025-04-05 15:54:50.799837','qrcodes/DEFAULT_202504041554.png',1,'f2954836-1bd3-4885-aa87-4e97d274c1e8'),(58,'7cae3336dbbe4541a239c3c61bba7bac','2025-04-04 16:09:03.316493','2025-04-05 16:09:03.309255','qrcodes/DEFAULT_202504041609.png',1,'7cae3336-dbbe-4541-a239-c3c61bba7bac'),(59,'c2ba5c9b4b494849bca1b2b6649cb268','2025-04-04 16:25:38.169424','2025-04-05 16:25:38.151115','qrcodes/DEFAULT_202504041625.png',1,'c2ba5c9b-4b49-4849-bca1-b2b6649cb268'),(60,'b69b1cbc8b9b40919ecd2bbd5c75a19e','2025-04-04 16:27:15.309616','2025-04-05 16:27:15.302509','qrcodes/DEFAULT_202504041627.png',1,'b69b1cbc-8b9b-4091-9ecd-2bbd5c75a19e'),(61,'eaf2ffaa57644ea58c99c4d8e738c872','2025-04-05 06:34:47.778578','2025-04-06 06:34:47.753429','qrcodes/DEFAULT_202504050634.png',1,'eaf2ffaa-5764-4ea5-8c99-c4d8e738c872'),(62,'906298392154416db3e5b1e4abaf46a8','2025-04-05 06:47:10.902140','2025-04-06 06:47:10.885789','qrcodes/DEFAULT_202504050647.png',1,'90629839-2154-416d-b3e5-b1e4abaf46a8'),(63,'85ce4abec59a40d58b4906f2bf9c68f8','2025-04-05 07:17:03.302143','2025-04-06 07:17:03.287607','qrcodes/DEFAULT_202504050717.png',1,'85ce4abe-c59a-40d5-8b49-06f2bf9c68f8'),(66,'a8cfd8c1091d41cf8c7248e475d1e78f','2025-04-06 12:05:16.883152','2025-04-06 15:59:59.859831','qrcodes/DEFAULT_202504061205.png',1,'a8cfd8c1-091d-41cf-8c72-48e475d1e78f'),(68,'d706eb6c285048c5ad9dd560203328b9','2025-04-07 07:27:47.617023','2025-04-07 15:59:59.584938','qrcodes/DEFAULT_202504070727.png',1,'d706eb6c-2850-48c5-ad9d-d560203328b9'),(70,'41bcfdeea53e44ec997c06c9343fa503','2025-04-08 04:46:49.566529','2025-04-08 05:16:42.589531','qrcodes/DEFAULT_202504080446.png',1,'41bcfdee-a53e-44ec-997c-06c9343fa503'),(71,'21ef75c774a146f59b17aefee7cd4378','2025-04-08 05:16:48.309984','2025-04-08 11:49:56.147715','qrcodes/DEFAULT_202504080516.png',1,'21ef75c7-74a1-46f5-9b17-aefee7cd4378'),(72,'9c7def01d3c04effbcfa75084d631f61','2025-04-08 11:50:11.200656','2025-04-08 15:59:59.166919','qrcodes/DEFAULT_202504081150.png',1,'9c7def01-d3c0-4eff-bcfa-75084d631f61'),(73,'45e5874670d44d1180632114d0bc0f41','2025-04-09 05:58:11.412369','2025-04-09 15:59:59.383276','qrcodes/DEFAULT_202504090558.png',1,'45e58746-70d4-4d11-8063-2114d0bc0f41');
/*!40000 ALTER TABLE `attendance_qrcode` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `attendance_waitingqueue`
--

DROP TABLE IF EXISTS `attendance_waitingqueue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance_waitingqueue` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `join_time` datetime(6) NOT NULL,
  `estimated_wait_time` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `session_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  `practice_record_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `attendance_waitingqu_session_id_d10d4199_fk_attendanc` (`session_id`),
  KEY `attendance_waitingqu_student_id_d6394e92_fk_students_` (`student_id`),
  KEY `attendance_waitingqu_practice_record_id_cb2b4e6b_fk_students_` (`practice_record_id`),
  CONSTRAINT `attendance_waitingqu_practice_record_id_cb2b4e6b_fk_students_` FOREIGN KEY (`practice_record_id`) REFERENCES `students_practicerecord` (`id`),
  CONSTRAINT `attendance_waitingqu_session_id_d10d4199_fk_attendanc` FOREIGN KEY (`session_id`) REFERENCES `attendance_attendancesession` (`id`),
  CONSTRAINT `attendance_waitingqu_student_id_d6394e92_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance_waitingqueue`
--

LOCK TABLES `attendance_waitingqueue` WRITE;
/*!40000 ALTER TABLE `attendance_waitingqueue` DISABLE KEYS */;
INSERT INTO `attendance_waitingqueue` VALUES (3,'2025-04-08 08:45:21.948915',0,0,26,3,NULL),(4,'2025-04-08 12:02:55.294784',38,0,27,3,NULL),(5,'2025-04-09 14:11:39.937534',-5,0,28,3,NULL),(6,'2025-04-09 14:59:38.770408',66,0,28,3,NULL);
/*!40000 ALTER TABLE `attendance_waitingqueue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=121 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can view permission',1,'view_permission'),(5,'Can add group',2,'add_group'),(6,'Can change group',2,'change_group'),(7,'Can delete group',2,'delete_group'),(8,'Can view group',2,'view_group'),(9,'Can add content type',3,'add_contenttype'),(10,'Can change content type',3,'change_contenttype'),(11,'Can delete content type',3,'delete_contenttype'),(12,'Can view content type',3,'view_contenttype'),(13,'Can add 用户',4,'add_user'),(14,'Can change 用户',4,'change_user'),(15,'Can delete 用户',4,'delete_user'),(16,'Can view 用户',4,'view_user'),(17,'Can add 学生收藏',5,'add_studentfavorite'),(18,'Can change 学生收藏',5,'change_studentfavorite'),(19,'Can delete 学生收藏',5,'delete_studentfavorite'),(20,'Can view 学生收藏',5,'view_studentfavorite'),(21,'Can add 学生',6,'add_student'),(22,'Can change 学生',6,'change_student'),(23,'Can delete 学生',6,'delete_student'),(24,'Can view 学生',6,'view_student'),(25,'Can add 练琴记录',7,'add_practicerecord'),(26,'Can change 练琴记录',7,'change_practicerecord'),(27,'Can delete 练琴记录',7,'delete_practicerecord'),(28,'Can view 练琴记录',7,'view_practicerecord'),(29,'Can add 考勤记录',8,'add_attendance'),(30,'Can change 考勤记录',8,'change_attendance'),(31,'Can delete 考勤记录',8,'delete_attendance'),(32,'Can view 考勤记录',8,'view_attendance'),(33,'Can add 曲谱页面',9,'add_sheetmusicpage'),(34,'Can change 曲谱页面',9,'change_sheetmusicpage'),(35,'Can delete 曲谱页面',9,'delete_sheetmusicpage'),(36,'Can view 曲谱页面',9,'view_sheetmusicpage'),(37,'Can add 曲谱',10,'add_sheetmusic'),(38,'Can change 曲谱',10,'change_sheetmusic'),(39,'Can delete 曲谱',10,'delete_sheetmusic'),(40,'Can view 曲谱',10,'view_sheetmusic'),(41,'Can add 教师信息',11,'add_teacherprofile'),(42,'Can change 教师信息',11,'change_teacherprofile'),(43,'Can delete 教师信息',11,'delete_teacherprofile'),(44,'Can view 教师信息',11,'view_teacherprofile'),(45,'Can add 隐私设置',12,'add_privacysetting'),(46,'Can change 隐私设置',12,'change_privacysetting'),(47,'Can delete 隐私设置',12,'delete_privacysetting'),(48,'Can view 隐私设置',12,'view_privacysetting'),(49,'Can add 教师证书',13,'add_teachercertificate'),(50,'Can change 教师证书',13,'change_teachercertificate'),(51,'Can delete 教师证书',13,'delete_teachercertificate'),(52,'Can view 教师证书',13,'view_teachercertificate'),(53,'Can add 通知设置',14,'add_notificationsetting'),(54,'Can change 通知设置',14,'change_notificationsetting'),(55,'Can delete 通知设置',14,'delete_notificationsetting'),(56,'Can view 通知设置',14,'view_notificationsetting'),(57,'Can add 钢琴',15,'add_piano'),(58,'Can change 钢琴',15,'change_piano'),(59,'Can delete 钢琴',15,'delete_piano'),(60,'Can view 钢琴',15,'view_piano'),(61,'Can add 课程安排',16,'add_courseschedule'),(62,'Can change 课程安排',16,'change_courseschedule'),(63,'Can delete 课程安排',16,'delete_courseschedule'),(64,'Can view 课程安排',16,'view_courseschedule'),(65,'Can add 课程',17,'add_course'),(66,'Can change 课程',17,'change_course'),(67,'Can delete 课程',17,'delete_course'),(68,'Can view 课程',17,'view_course'),(69,'Can add 钢琴等级',18,'add_pianolevel'),(70,'Can change 钢琴等级',18,'change_pianolevel'),(71,'Can delete 钢琴等级',18,'delete_pianolevel'),(72,'Can view 钢琴等级',18,'view_pianolevel'),(73,'Can add 曲谱',19,'add_sheetmusic'),(74,'Can change 曲谱',19,'change_sheetmusic'),(75,'Can delete 曲谱',19,'delete_sheetmusic'),(76,'Can view 曲谱',19,'view_sheetmusic'),(77,'Can add 财务报表',20,'add_financialstatement'),(78,'Can change 财务报表',20,'change_financialstatement'),(79,'Can delete 财务报表',20,'delete_financialstatement'),(80,'Can view 财务报表',20,'view_financialstatement'),(81,'Can add 付款类别',21,'add_paymentcategory'),(82,'Can change 付款类别',21,'change_paymentcategory'),(83,'Can delete 付款类别',21,'delete_paymentcategory'),(84,'Can view 付款类别',21,'view_paymentcategory'),(85,'Can add 付款记录',22,'add_payment'),(86,'Can change 付款记录',22,'change_payment'),(87,'Can delete 付款记录',22,'delete_payment'),(88,'Can view 付款记录',22,'view_payment'),(89,'Can add 费用标准',23,'add_fee'),(90,'Can change 费用标准',23,'change_fee'),(91,'Can delete 费用标准',23,'delete_fee'),(92,'Can view 费用标准',23,'view_fee'),(93,'Can add 考勤记录',24,'add_attendancerecord'),(94,'Can change 考勤记录',24,'change_attendancerecord'),(95,'Can delete 考勤记录',24,'delete_attendancerecord'),(96,'Can view 考勤记录',24,'view_attendancerecord'),(97,'Can add 二维码',25,'add_qrcode'),(98,'Can change 二维码',25,'change_qrcode'),(99,'Can delete 二维码',25,'delete_qrcode'),(100,'Can view 二维码',25,'view_qrcode'),(101,'Can add 等待队列',26,'add_waitingqueue'),(102,'Can change 等待队列',26,'change_waitingqueue'),(103,'Can delete 等待队列',26,'delete_waitingqueue'),(104,'Can view 等待队列',26,'view_waitingqueue'),(105,'Can add 考勤会话',27,'add_attendancesession'),(106,'Can change 考勤会话',27,'change_attendancesession'),(107,'Can delete 考勤会话',27,'delete_attendancesession'),(108,'Can view 考勤会话',27,'view_attendancesession'),(109,'Can add session',28,'add_session'),(110,'Can change session',28,'change_session'),(111,'Can delete session',28,'delete_session'),(112,'Can view session',28,'view_session'),(113,'Can add log entry',29,'add_logentry'),(114,'Can change log entry',29,'change_logentry'),(115,'Can delete log entry',29,'delete_logentry'),(116,'Can view log entry',29,'view_logentry'),(117,'Can add 钢琴分配',30,'add_pianoassignment'),(118,'Can change 钢琴分配',30,'change_pianoassignment'),(119,'Can delete 钢琴分配',30,'delete_pianoassignment'),(120,'Can view 钢琴分配',30,'view_pianoassignment');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_course`
--

DROP TABLE IF EXISTS `courses_course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_course` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration` bigint NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `level_id` bigint NOT NULL,
  `teacher_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `courses_course_level_id_be3d7088_fk_courses_pianolevel_id` (`level_id`),
  KEY `courses_course_teacher_id_846fa526_fk_teachers_teacherprofile_id` (`teacher_id`),
  CONSTRAINT `courses_course_level_id_be3d7088_fk_courses_pianolevel_id` FOREIGN KEY (`level_id`) REFERENCES `courses_pianolevel` (`id`),
  CONSTRAINT `courses_course_teacher_id_846fa526_fk_teachers_teacherprofile_id` FOREIGN KEY (`teacher_id`) REFERENCES `teachers_teacherprofile` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_course`
--

LOCK TABLES `courses_course` WRITE;
/*!40000 ALTER TABLE `courses_course` DISABLE KEYS */;
INSERT INTO `courses_course` VALUES (1,'通用考勤','DEFAULT','自动生成的通用考勤课程',1800000000,'2025-04-01 16:14:55.225820',1,1,2);
/*!40000 ALTER TABLE `courses_course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_course_students`
--

DROP TABLE IF EXISTS `courses_course_students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_course_students` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `course_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `courses_course_students_course_id_student_id_ccf0df20_uniq` (`course_id`,`student_id`),
  KEY `courses_course_stude_student_id_415c12f2_fk_students_` (`student_id`),
  CONSTRAINT `courses_course_stude_student_id_415c12f2_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`),
  CONSTRAINT `courses_course_students_course_id_2c36f816_fk_courses_course_id` FOREIGN KEY (`course_id`) REFERENCES `courses_course` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_course_students`
--

LOCK TABLES `courses_course_students` WRITE;
/*!40000 ALTER TABLE `courses_course_students` DISABLE KEYS */;
INSERT INTO `courses_course_students` VALUES (1,1,1),(3,1,2),(4,1,3);
/*!40000 ALTER TABLE `courses_course_students` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_courseschedule`
--

DROP TABLE IF EXISTS `courses_courseschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_courseschedule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `weekday` int NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `course_id` bigint NOT NULL,
  `is_temporary` tinyint(1) NOT NULL,
  `location` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_course_schedule` (`course_id`,`weekday`,`start_time`),
  KEY `courses_courseschedule_course_id_a4d2058b` (`course_id`),
  CONSTRAINT `courses_courseschedule_course_id_a4d2058b_fk_courses_course_id` FOREIGN KEY (`course_id`) REFERENCES `courses_course` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_courseschedule`
--

LOCK TABLES `courses_courseschedule` WRITE;
/*!40000 ALTER TABLE `courses_courseschedule` DISABLE KEYS */;
INSERT INTO `courses_courseschedule` VALUES (1,1,'18:02:12.043940','20:02:12.043940',1,1,1,''),(2,2,'02:08:43.000745','04:08:43.000745',1,1,1,''),(3,4,'16:27:15.302509','23:59:59.999999',1,1,1,''),(4,5,'06:34:47.753429','23:59:59.999999',1,1,1,''),(5,5,'06:47:10.885789','23:59:59.999999',1,1,1,''),(6,5,'07:17:03.287607','23:59:59.999999',1,1,1,''),(7,6,'07:41:33.705850','23:59:59.999999',1,1,1,''),(8,6,'19:05:48.821409','23:59:59.999999',1,1,1,''),(9,6,'20:05:16.859831','23:59:59.859831',1,1,1,''),(10,0,'12:29:54.475499','23:59:59.475499',1,1,1,''),(11,0,'15:27:47.584938','23:59:59.584938',1,1,1,''),(12,1,'12:15:03.934102','23:59:59.934102',1,1,1,''),(13,1,'12:46:49.553776','23:59:59.553776',1,1,1,''),(14,1,'13:16:48.288791','23:59:59.288791',1,1,1,''),(15,1,'19:50:11.166919','23:59:59.166919',1,1,1,''),(16,2,'13:58:11.383276','23:59:59.383276',1,1,1,'');
/*!40000 ALTER TABLE `courses_courseschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_piano`
--

DROP TABLE IF EXISTS `courses_piano`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_piano` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `number` int NOT NULL,
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `purchase_date` date DEFAULT NULL,
  `last_tuned_date` date DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_occupied` tinyint(1) NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_reserved` tinyint(1) NOT NULL,
  `reserved_for_id` bigint DEFAULT NULL,
  `reserved_until` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `number` (`number`),
  KEY `courses_piano_reserved_for_id_be60a6af_fk_students_student_id` (`reserved_for_id`),
  CONSTRAINT `courses_piano_reserved_for_id_be60a6af_fk_students_student_id` FOREIGN KEY (`reserved_for_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_piano`
--

LOCK TABLES `courses_piano` WRITE;
/*!40000 ALTER TABLE `courses_piano` DISABLE KEYS */;
INSERT INTO `courses_piano` VALUES (1,1,'雅马哈','01','2025-04-02','2025-04-02',1,0,'维护: 调音 - 2025-04-07 08:55\n恢复使用: 2025-04-07 08:55',0,NULL,NULL),(2,2,'YAMAHA','02','2025-04-02','2025-04-02',1,0,'',0,NULL,NULL);
/*!40000 ALTER TABLE `courses_piano` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_pianolevel`
--

DROP TABLE IF EXISTS `courses_pianolevel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_pianolevel` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `level` int NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `level` (`level`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_pianolevel`
--

LOCK TABLES `courses_pianolevel` WRITE;
/*!40000 ALTER TABLE `courses_pianolevel` DISABLE KEYS */;
INSERT INTO `courses_pianolevel` VALUES (1,1,'初级');
/*!40000 ALTER TABLE `courses_pianolevel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `courses_sheetmusic`
--

DROP TABLE IF EXISTS `courses_sheetmusic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses_sheetmusic` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `composer` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `file` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cover_image` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `upload_date` datetime(6) NOT NULL,
  `is_public` tinyint(1) NOT NULL,
  `difficulty` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `style` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `period` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level_id` bigint DEFAULT NULL,
  `uploaded_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `courses_sheetmusic_level_id_ae0c646f_fk_courses_pianolevel_id` (`level_id`),
  KEY `courses_sheetmusic_uploaded_by_id_c47059ce_fk_users_user_id` (`uploaded_by_id`),
  CONSTRAINT `courses_sheetmusic_level_id_ae0c646f_fk_courses_pianolevel_id` FOREIGN KEY (`level_id`) REFERENCES `courses_pianolevel` (`id`),
  CONSTRAINT `courses_sheetmusic_uploaded_by_id_c47059ce_fk_users_user_id` FOREIGN KEY (`uploaded_by_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses_sheetmusic`
--

LOCK TABLES `courses_sheetmusic` WRITE;
/*!40000 ALTER TABLE `courses_sheetmusic` DISABLE KEYS */;
INSERT INTO `courses_sheetmusic` VALUES (3,'卡农','姚博文','1','sheet_music/PDF_123498954.pdf','sheet_music/covers/带身份证照.jpg','2025-04-02 06:46:17.801589',1,'中级','古典','古典主义',1,2),(4,'卡农','姚博文','1','sheet_music/PDF_123498954_MiUD1gY.pdf','sheet_music/covers/带身份证照_0XVNy11.jpg','2025-04-02 06:47:44.091033',1,'中级','古典','古典主义',1,2),(6,'卡农','姚博文','','sheet_music/ũ1.jpg','sheet_music/covers/f2b248c7e5f64298aa519c017930db43_8Ey50Q9.png','2025-04-07 04:21:15.971056',1,'初级','古典','古典主义',1,2);
/*!40000 ALTER TABLE `courses_sheetmusic` ENABLE KEYS */;
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
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2025-04-02 02:58:07.420817','1','钢琴-1',1,'[{\"added\": {}}]',15,1),(2,'2025-04-02 04:18:41.060454','2','钢琴-2',1,'[{\"added\": {}}]',15,1),(3,'2025-04-06 07:53:13.326252','13','未关联课程 - 2025-04-04 15:27',3,'',27,1),(4,'2025-04-06 07:53:13.330870','12','未关联课程 - 2025-04-04 15:09',3,'',27,1),(5,'2025-04-06 11:10:43.662084','65','二维码-通用考勤-2025-04-06 19:05',3,'',25,1),(6,'2025-04-07 04:35:39.640766','64','二维码-通用考勤-2025-04-06 07:41',3,'',25,1),(7,'2025-04-07 04:36:25.818616','1','王止舟 - 2025-04-06 12:54',3,'',26,1),(8,'2025-04-07 06:00:37.426025','1','张三 - 2025-04-04',3,'',7,1),(9,'2025-04-07 06:11:35.454671','9','王止舟 - 2025-04-06',3,'',7,1),(10,'2025-04-07 07:28:43.463559','14','王止舟 - 2025-04-07',3,'',7,1),(11,'2025-04-07 07:28:43.466560','13','张三 - 2025-04-07',3,'',7,1),(12,'2025-04-07 07:28:43.468273','12','李四 - 2025-04-07',3,'',7,1),(13,'2025-04-07 11:55:05.155883','67','二维码-通用考勤-2025-04-07 04:29',3,'',25,1),(14,'2025-04-07 15:35:41.706583','20','张三 - 2025-04-07',3,'',7,1),(15,'2025-04-07 15:35:41.708315','19','李四 - 2025-04-07',3,'',7,1),(16,'2025-04-07 15:35:41.709317','18','李四 - 2025-04-07',3,'',7,1),(17,'2025-04-08 04:10:27.686820','22','王止舟 - 2025-04-07',3,'',7,1),(18,'2025-04-08 04:38:58.374001','2','王止舟 - 2025-04-07 08:45',3,'',26,1),(19,'2025-04-08 05:15:55.567655','69','二维码-通用考勤-2025-04-08 04:15',3,'',25,1),(20,'2025-04-08 11:48:56.779206','25','李四 - 2025-04-08',3,'',7,1),(21,'2025-04-08 11:48:56.781229','24','李四 - 2025-04-08',3,'',7,1),(22,'2025-04-08 11:48:56.783136','26','张三 - 2025-04-08',3,'',7,1),(23,'2025-04-08 11:49:12.312853','23','张三 - 2025-04-08',3,'',7,1),(24,'2025-04-08 15:18:08.040877','29','王止舟 - 2025-04-08',3,'',7,1),(25,'2025-04-08 15:30:23.789355','28','李四 - 2025-04-08',3,'',7,1),(26,'2025-04-09 05:55:44.772201','31','王止舟 - 2025-04-08',3,'',7,1),(27,'2025-04-09 05:55:44.774865','30','李四 - 2025-04-08',3,'',7,1),(28,'2025-04-09 14:32:11.429191','37','李四 - 2025-04-09',3,'',7,1),(29,'2025-04-09 14:32:11.432242','36','张三 - 2025-04-09',3,'',7,1),(30,'2025-04-09 14:32:21.137412','35','李四 - 2025-04-09',3,'',7,1),(31,'2025-04-09 14:32:21.140040','34','张三 - 2025-04-09',3,'',7,1);
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
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (29,'admin','logentry'),(24,'attendance','attendancerecord'),(27,'attendance','attendancesession'),(30,'attendance','pianoassignment'),(25,'attendance','qrcode'),(26,'attendance','waitingqueue'),(2,'auth','group'),(1,'auth','permission'),(3,'contenttypes','contenttype'),(17,'courses','course'),(16,'courses','courseschedule'),(15,'courses','piano'),(18,'courses','pianolevel'),(19,'courses','sheetmusic'),(23,'finance','fee'),(20,'finance','financialstatement'),(22,'finance','payment'),(21,'finance','paymentcategory'),(28,'sessions','session'),(8,'students','attendance'),(7,'students','practicerecord'),(10,'students','sheetmusic'),(9,'students','sheetmusicpage'),(6,'students','student'),(5,'students','studentfavorite'),(14,'teachers','notificationsetting'),(12,'teachers','privacysetting'),(13,'teachers','teachercertificate'),(11,'teachers','teacherprofile'),(4,'users','user');
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
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-04-01 12:43:31.298133'),(2,'contenttypes','0002_remove_content_type_name','2025-04-01 12:44:05.636648'),(3,'auth','0001_initial','2025-04-01 12:44:05.779779'),(4,'auth','0002_alter_permission_name_max_length','2025-04-01 12:44:05.812577'),(5,'auth','0003_alter_user_email_max_length','2025-04-01 12:44:05.820104'),(6,'auth','0004_alter_user_username_opts','2025-04-01 12:44:05.824136'),(7,'auth','0005_alter_user_last_login_null','2025-04-01 12:44:05.828558'),(8,'auth','0006_require_contenttypes_0002','2025-04-01 12:44:05.832586'),(9,'auth','0007_alter_validators_add_error_messages','2025-04-01 12:44:05.836594'),(10,'auth','0008_alter_user_username_max_length','2025-04-01 12:44:05.840622'),(11,'auth','0009_alter_user_last_name_max_length','2025-04-01 12:44:05.844937'),(12,'auth','0010_alter_group_name_max_length','2025-04-01 12:44:05.857045'),(13,'auth','0011_update_proxy_permissions','2025-04-01 12:44:05.861050'),(14,'auth','0012_alter_user_first_name_max_length','2025-04-01 12:44:05.865070'),(15,'users','0001_initial','2025-04-01 12:44:06.051687'),(16,'students','0001_initial','2025-04-01 12:44:21.742889'),(18,'courses','0001_initial','2025-04-01 12:44:35.377219'),(19,'finance','0001_initial','2025-04-01 12:44:42.997415'),(20,'attendance','0001_initial','2025-04-01 12:44:49.598764'),(21,'sessions','0001_initial','2025-04-01 12:45:06.569792'),(22,'admin','0001_initial','2025-04-01 12:46:18.370245'),(23,'admin','0002_logentry_remove_auto_add','2025-04-01 12:46:26.925529'),(24,'admin','0003_logentry_add_action_flag_choices','2025-04-01 12:46:26.934533'),(25,'attendance','0002_qrcode_code','2025-04-01 13:51:12.732262'),(26,'courses','0002_alter_pianolevel_level','2025-04-01 15:52:31.537594'),(27,'courses','0003_courseschedule_is_temporary','2025-04-01 18:00:59.717440'),(28,'attendance','0003_attendancesession_description','2025-04-01 18:01:21.240696'),(29,'attendance','0004_attendancerecord_check_in_method_and_more','2025-04-02 10:38:33.199271'),(30,'attendance','0005_attendancesession_is_active_and_more','2025-04-04 14:48:06.053689'),(31,'courses','0004_alter_courseschedule_options_and_more','2025-04-04 16:26:45.017133'),(32,'students','0002_practicerecord_status_alter_practicerecord_duration_and_more','2025-04-05 09:05:08.124388'),(33,'students','0003_alter_attendance_options_and_more','2025-04-06 08:19:57.061549'),(34,'students','0004_alter_sheetmusicpage_unique_together_and_more','2025-04-06 18:54:15.754554'),(36,'attendance','0006_pianoassignment','2025-04-06 13:44:22.799746'),(37,'courses','0005_piano_is_reserved_piano_reserved_for_and_more','2025-04-07 15:31:14.143766'),(39,'attendance','0007_waitingqueue_practice_record','2025-04-08 12:37:06.749330');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('0cpcxyzf7x6eudwmpy17hqpbxsdhfw11','.eJxVjMsOwiAUBf-FtSEU24t26d5vINwHFjVgSptojP9um3Sh2zNz5q18mKfBz1VGn1j1yqrd74aBbpJXwNeQL0VTydOYUK-K3mjV58JyP23uX2AIdVjeCE0UROo4CnUBKQCZtqEInUVHzoCAWMsLMDYC74UwAMsBXdscHazRKrWmkr08H2l8qd58vgFQQN8:1tzcRI:Wy2xvdKfHuU9kX17ZweYHFvl0Nd3EkwFBe2jfjDmUPc','2025-04-15 14:18:04.050613'),('2yxtf1zhc77giwcq5pk68505jjiobu75','.eJxVjDsOwjAQBe_iGln-xJ9Q0nMGa71eiAHZKE4kEOLuJCgFtDPz3osFmKchzI3GkBPbM812vywCXqmsIl2gnCvHWqYxR74mfLONH2ui22Fr_w4GaMOy7iVIZ0yHCaM03iWUNjmPVsQFKqd77bUXSiCp3iqrQWHsTiTBGEv-e9qotVxLoMc9j0-2F-8PZEs-gQ:1u21dU:3O0CBfuP0J4kGUusgwZ1qqO9q5pSUPG6J4YvONy79TY','2025-04-22 05:36:36.004757'),('4ddyl7k9f25pv2ikvnxeyliao8t1wliq','.eJxVjDsOwjAQBe_iGln-xJ9Q0nMGa71eiAHZKE4kEOLuJCgFtDPz3osFmKchzI3GkBPbM812vywCXqmsIl2gnCvHWqYxR74mfLONH2ui22Fr_w4GaMOy7iVIZ0yHCaM03iWUNjmPVsQFKqd77bUXSiCp3iqrQWHsTiTBGEv-e9qotVxLoMc9j0-2F-8PZEs-gQ:1u223i:e7koHu7t98wk9pW6LiGhkLW7t5YO3BGt_WUsMFl6BJw','2025-04-22 06:03:42.232193'),('afaoi8el1kyeu3cc0tqq8w65t0eah0gq','.eJxVjE0OwiAYBe_C2hAKFaRL956B8P1gUQOmtInGeHdt0oVu38yblwhxmcewNJ5CJjEILXa_G0S8clkBXWI5V4m1zFMGuSpyo02eKvHtuLl_gTG28ft2Gl23R7a9cZiIlPeQjD1gMl2n0QNHMMTJgUtgPUXfqV4TgtUqJdOv0cat5VoCP-55eopBvT-4TkAE:1u4FSP:9CTScY1XMYT95amD20JJ4JtBrqRG2-oqbsuxNGlK2yM','2025-04-28 08:46:21.033269'),('agyxklmvmkvnuqpwks1sfbxqaz8vdrv7','.eJxVjMsOwiAQRf-FtSFToJ3SpXu_gQwvixow0CYa479rky50e8-558UMrcts1haqSZ5NrGeH382Su4a8AX-hfC7clbzUZPmm8J02fio-3I67-xeYqc3ftxIoFaKFDqP2qHqNNiBEhyBHQVE41HIQilznBogUaUQYI3qJMGgtt2gLraWSTXjcU32yCd4fVeo-PA:1u26iC:_AySlrHr2KA5IJy2DQ5U3wfl9Y6nC24KaDP8E2FKvuY','2025-04-22 11:01:48.476472'),('bfflnd7jxlcfz2a4j4kjzk9shgnddcnm','.eJxVjMsOwiAUBf-FtSEU24t26d5vINwHFjVgSptojP9um3Sh2zNz5q18mKfBz1VGn1j1yqrd74aBbpJXwNeQL0VTydOYUK-K3mjV58JyP23uX2AIdVjeCE0UROo4CnUBKQCZtqEInUVHzoCAWMsLMDYC74UwAMsBXdscHazRKrWmkr08H2l8qd58vgFQQN8:1tzfSx:1_6K84TjyXSJzkr_M-Gzmhj2o5AchRk_vFLxQMJiq2Y','2025-04-15 17:31:59.899986'),('hv7nv5aw9whh47m0udg2q1agy6jou5nz','.eJxVjDsOwjAQBe_iGln-xJ9Q0nMGa71eiAHZKE4kEOLuJCgFtDPz3osFmKchzI3GkBPbM812vywCXqmsIl2gnCvHWqYxR74mfLONH2ui22Fr_w4GaMOy7iVIZ0yHCaM03iWUNjmPVsQFKqd77bUXSiCp3iqrQWHsTiTBGEv-e9qotVxLoMc9j0-2F-8PZEs-gQ:1tzfSK:w4WNi7B7uE7MBGn-FB-icnx4DH9fRvvM3IlyG6NFxFc','2025-04-15 17:31:20.054992'),('n2ihg3jm8whsu4i2b7spkhd0i5wl1rya','.eJxVjMsOwiAQRf-FtSFToJ3SpXu_gQwvixow0CYa479rky50e8-558UMrcts1haqSZ5NrGeH382Su4a8AX-hfC7clbzUZPmm8J02fio-3I67-xeYqc3ftxIoFaKFDqP2qHqNNiBEhyBHQVE41HIQilznBogUaUQYI3qJMGgtt2gLraWSTXjcU32yCd4fVeo-PA:1u28I4:6YURhOTZpS-suK7lg66LFiltq2H8XwkwgVEruRdN83U','2025-04-22 12:42:56.595609'),('ne8nr78mxh78qwgy7oma6di35iv9b94v','.eJxVjMsOwiAUBf-FtSEU24t26d5vINwHFjVgSptojP9um3Sh2zNz5q18mKfBz1VGn1j1yqrd74aBbpJXwNeQL0VTydOYUK-K3mjV58JyP23uX2AIdVjeCE0UROo4CnUBKQCZtqEInUVHzoCAWMsLMDYC74UwAMsBXdscHazRKrWmkr08H2l8qd58vgFQQN8:1tzeaD:7aJANKk6O5jdjl3lHGFu4upMhrth61gveOfLA4vcXmw','2025-04-15 16:35:25.077717'),('qkspg3d5n1hxml0c7lcjtlg59gzofpce','.eJxVjMsOwiAUBf-FtSEU24t26d5vINwHFjVgSptojP9um3Sh2zNz5q18mKfBz1VGn1j1yqrd74aBbpJXwNeQL0VTydOYUK-K3mjV58JyP23uX2AIdVjeCE0UROo4CnUBKQCZtqEInUVHzoCAWMsLMDYC74UwAMsBXdscHazRKrWmkr08H2l8qd58vgFQQN8:1u008x:1lib3PbiO-MVzFtSZWTtR7qmPFURRamLJ4JEhjm9viw','2025-04-16 15:36:43.893273'),('sc2ll5kbgcqm9nl5saaul6pe33defuy2','.eJxVjMsOwiAUBf-FtSEU24t26d5vINwHFjVgSptojP9um3Sh2zNz5q18mKfBz1VGn1j1yqrd74aBbpJXwNeQL0VTydOYUK-K3mjV58JyP23uX2AIdVjeCE0UROo4CnUBKQCZtqEInUVHzoCAWMsLMDYC74UwAMsBXdscHazRKrWmkr08H2l8qd58vgFQQN8:1tzcz8:eTQLRboatl9NtmNCGGwUvZVmnvZ0WiBTegJZ31DQTBI','2025-04-15 14:53:02.558091'),('shibyluxkbytrtpfpspug89u4uh6b3qb','.eJxVjMsOwiAQRf-FtSFToJ3SpXu_gQwvixow0CYa479rky50e8-558UMrcts1haqSZ5NrGeH382Su4a8AX-hfC7clbzUZPmm8J02fio-3I67-xeYqc3ftxIoFaKFDqP2qHqNNiBEhyBHQVE41HIQilznBogUaUQYI3qJMGgtt2gLraWSTXjcU32yCd4fVeo-PA:1u2BNQ:o7TVgqFbD1_t_mQ88MjpA-IZPBrnptHra6WnRlxTRuo','2025-04-22 16:00:40.879419');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `finance_fee`
--

DROP TABLE IF EXISTS `finance_fee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `finance_fee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `category_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `finance_fee_category_id_72ad6fdd_fk_finance_paymentcategory_id` (`category_id`),
  CONSTRAINT `finance_fee_category_id_72ad6fdd_fk_finance_paymentcategory_id` FOREIGN KEY (`category_id`) REFERENCES `finance_paymentcategory` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `finance_fee`
--

LOCK TABLES `finance_fee` WRITE;
/*!40000 ALTER TABLE `finance_fee` DISABLE KEYS */;
/*!40000 ALTER TABLE `finance_fee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `finance_financialstatement`
--

DROP TABLE IF EXISTS `finance_financialstatement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `finance_financialstatement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `period` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `total_income` decimal(10,2) NOT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `generated_at` datetime(6) NOT NULL,
  `generated_by_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `finance_financialsta_generated_by_id_1a061f50_fk_users_use` (`generated_by_id`),
  CONSTRAINT `finance_financialsta_generated_by_id_1a061f50_fk_users_use` FOREIGN KEY (`generated_by_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `finance_financialstatement`
--

LOCK TABLES `finance_financialstatement` WRITE;
/*!40000 ALTER TABLE `finance_financialstatement` DISABLE KEYS */;
/*!40000 ALTER TABLE `finance_financialstatement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `finance_payment`
--

DROP TABLE IF EXISTS `finance_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `finance_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_date` date DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `notes` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `category_id` bigint NOT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `finance_payment_category_id_85bb0dcf_fk_finance_p` (`category_id`),
  KEY `finance_payment_created_by_id_d7a8491e_fk_users_user_id` (`created_by_id`),
  KEY `finance_payment_student_id_07a30e9c_fk_students_student_id` (`student_id`),
  CONSTRAINT `finance_payment_category_id_85bb0dcf_fk_finance_p` FOREIGN KEY (`category_id`) REFERENCES `finance_paymentcategory` (`id`),
  CONSTRAINT `finance_payment_created_by_id_d7a8491e_fk_users_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `users_user` (`id`),
  CONSTRAINT `finance_payment_student_id_07a30e9c_fk_students_student_id` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `finance_payment`
--

LOCK TABLES `finance_payment` WRITE;
/*!40000 ALTER TABLE `finance_payment` DISABLE KEYS */;
INSERT INTO `finance_payment` VALUES (1,1111.00,'cash','paid','2025-04-04',NULL,'','2025-04-04 08:31:38.448359','2025-04-04 09:16:42.963435',1,2,2),(2,2222.00,'cash','paid','2025-04-04',NULL,'','2025-04-04 11:26:10.716201','2025-04-04 11:26:22.223824',2,2,1),(3,11111.00,'cash','paid','2025-04-04',NULL,'','2025-04-04 12:15:19.834157','2025-04-04 12:15:19.834157',1,2,2);
/*!40000 ALTER TABLE `finance_payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `finance_paymentcategory`
--

DROP TABLE IF EXISTS `finance_paymentcategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `finance_paymentcategory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `finance_paymentcategory`
--

LOCK TABLES `finance_paymentcategory` WRITE;
/*!40000 ALTER TABLE `finance_paymentcategory` DISABLE KEYS */;
INSERT INTO `finance_paymentcategory` VALUES (1,'学费','学生的教学费用'),(2,'书本费','购买教材和曲谱的费用');
/*!40000 ALTER TABLE `finance_paymentcategory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_attendance`
--

DROP TABLE IF EXISTS `students_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_attendance` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `check_in_time` datetime(6) NOT NULL,
  `check_out_time` datetime(6) DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_attendance_student_id_95d59851_fk_students_student_id` (`student_id`),
  CONSTRAINT `students_attendance_student_id_95d59851_fk_students_student_id` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_attendance`
--

LOCK TABLES `students_attendance` WRITE;
/*!40000 ALTER TABLE `students_attendance` DISABLE KEYS */;
INSERT INTO `students_attendance` VALUES (1,'2025-04-05','2025-04-05 08:47:23.324502','2025-04-05 08:47:29.193178','present','2025-04-05 08:47:23.324502',1),(2,'2025-04-06','2025-04-06 07:47:07.153897','2025-04-06 08:37:07.168830','present','2025-04-06 08:37:07.177712',2),(3,'2025-04-06','2025-04-06 11:07:42.240103',NULL,'present','2025-04-06 11:07:42.245097',1),(4,'2025-04-07','2025-04-07 06:49:00.000000','2025-04-07 07:19:00.000000','present','2025-04-07 06:49:44.536002',3),(5,'2025-04-07','2025-04-07 06:53:00.000000','2025-04-07 08:31:57.920737','present','2025-04-07 06:54:02.066234',1),(6,'2025-04-07','2025-04-07 07:11:04.476442','2025-04-07 07:41:04.476442','present','2025-04-07 07:11:04.481947',2),(7,'2025-04-08','2025-04-08 06:04:25.877138','2025-04-08 13:15:10.774631','present','2025-04-08 06:04:25.888707',1),(8,'2025-04-08','2025-04-08 06:40:04.908007',NULL,'present','2025-04-08 06:40:04.919115',2),(9,'2025-04-08','2025-04-08 13:15:59.298964',NULL,'present','2025-04-08 13:15:59.305968',3),(10,'2025-04-09','2025-04-09 07:18:40.085155','2025-04-09 14:31:13.135203','present','2025-04-09 07:18:40.093262',1),(11,'2025-04-09','2025-04-09 07:20:31.993830','2025-04-09 15:49:58.458968','present','2025-04-09 07:20:32.004425',2);
/*!40000 ALTER TABLE `students_attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_practicerecord`
--

DROP TABLE IF EXISTS `students_practicerecord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_practicerecord` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `start_time` datetime(6) NOT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `duration` int DEFAULT NULL,
  `piano_number` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `student_id` bigint NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `attendance_session_id` bigint DEFAULT NULL,
  `piano_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_practicerec_student_id_4ef8d93c_fk_students_` (`student_id`),
  KEY `students_practicerec_attendance_session_i_4da7e24d_fk_attendanc` (`attendance_session_id`),
  KEY `students_practicerecord_piano_id_72e3bdcc_fk_courses_piano_id` (`piano_id`),
  CONSTRAINT `students_practicerec_attendance_session_i_4da7e24d_fk_attendanc` FOREIGN KEY (`attendance_session_id`) REFERENCES `attendance_attendancesession` (`id`),
  CONSTRAINT `students_practicerec_student_id_4ef8d93c_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`),
  CONSTRAINT `students_practicerecord_piano_id_72e3bdcc_fk_courses_piano_id` FOREIGN KEY (`piano_id`) REFERENCES `courses_piano` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_practicerecord`
--

LOCK TABLES `students_practicerecord` WRITE;
/*!40000 ALTER TABLE `students_practicerecord` DISABLE KEYS */;
INSERT INTO `students_practicerecord` VALUES (2,'2025-04-05','2025-04-05 08:47:23.334138','2025-04-05 08:47:29.193178',35,1,'2025-04-05 08:47:23.334138',1,'completed',NULL,NULL),(3,'2025-04-05','2025-04-05 10:17:30.541977',NULL,35,1,'2025-04-05 10:17:30.541977',1,'completed',NULL,NULL),(4,'2025-04-05','2025-04-05 12:22:05.515555',NULL,NULL,1,'2025-04-05 12:22:05.515555',1,'completed',NULL,NULL),(5,'2025-04-06','2025-04-06 05:43:30.622548','2025-04-06 07:18:05.493405',94,1,'2025-04-06 05:43:30.622548',1,'completed',NULL,NULL),(6,'2025-04-06','2025-04-06 07:47:07.153897','2025-04-06 08:37:07.168830',50,1,'2025-04-06 07:47:07.153897',2,'completed',NULL,NULL),(7,'2025-04-06','2025-04-06 11:07:42.240103','2025-04-06 13:07:42.240103',NULL,1,'2025-04-06 11:07:42.240103',1,'completed',18,NULL),(8,'2025-04-06','2025-04-06 12:53:23.775683','2025-04-06 14:53:23.775683',NULL,2,'2025-04-06 12:53:23.776686',2,'completed',18,NULL),(10,'2025-04-07','2025-04-07 06:49:00.000000','2025-04-07 07:19:00.000000',30,1,'2025-04-07 06:49:44.540027',3,'completed',22,NULL),(11,'2025-04-07','2025-04-07 06:53:00.000000','2025-04-07 07:23:00.000000',30,1,'2025-04-07 06:54:02.066234',1,'completed',21,NULL),(15,'2025-04-07','2025-04-07 07:20:06.422762','2025-04-07 07:50:06.422762',30,1,'2025-04-07 07:20:06.431815',2,'completed',21,NULL),(16,'2025-04-07','2025-04-07 07:21:19.158697','2025-04-07 07:51:19.158697',30,1,'2025-04-07 07:21:19.165954',3,'completed',20,NULL),(17,'2025-04-07','2025-04-07 07:55:52.756924','2025-04-07 08:31:57.920737',36,2,'2025-04-07 07:55:52.756924',1,'completed',23,NULL),(21,'2025-04-07','2025-04-07 13:02:22.636435','2025-04-07 15:02:22.636435',NULL,2,'2025-04-07 13:02:22.636435',3,'completed',23,NULL),(27,'2025-04-08','2025-04-08 11:57:18.290296','2025-04-08 13:15:10.774631',77,1,'2025-04-08 11:57:18.290296',1,'completed',27,NULL),(32,'2025-04-08','2025-04-08 15:34:49.823928','2025-04-09 05:56:07.777441',240,2,'2025-04-09 05:56:07.788592',3,'completed',27,NULL),(33,'2025-04-08','2025-04-08 15:32:02.517161','2025-04-09 05:56:07.792611',240,1,'2025-04-09 05:56:07.802765',2,'completed',27,NULL),(38,'2025-04-09','2025-04-09 14:37:21.891811','2025-04-09 15:44:36.171285',67,1,'2025-04-09 14:37:21.892812',1,'completed',28,NULL),(39,'2025-04-09','2025-04-09 14:37:49.834792','2025-04-09 15:49:58.458968',72,2,'2025-04-09 14:37:49.834792',2,'completed',28,NULL);
/*!40000 ALTER TABLE `students_practicerecord` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_student`
--

DROP TABLE IF EXISTS `students_student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_student` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` int NOT NULL,
  `target_level` int NOT NULL,
  `phone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `parent_phone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `school` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `students_student_user_id_56286dbb_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_student`
--

LOCK TABLES `students_student` WRITE;
/*!40000 ALTER TABLE `students_student` DISABLE KEYS */;
INSERT INTO `students_student` VALUES (1,'张三',1,10,'15308585539','王二麻子','17546096013','响水镇中心小学','2025-04-01 13:07:26.153885','2025-04-05 05:33:53.118204',3),(2,'李四',1,10,'17546096013','良质','18216716741','响水镇中心小学','2025-04-02 04:44:19.730643','2025-04-06 07:46:40.394098',4),(3,'王止舟',1,10,'','','','','2025-04-06 10:18:45.068878','2025-04-06 10:18:45.068878',5);
/*!40000 ALTER TABLE `students_student` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_studentfavorite`
--

DROP TABLE IF EXISTS `students_studentfavorite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_studentfavorite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `sheet_music_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_studentfavorite_student_id_sheet_music_id_ef86e8fb_uniq` (`student_id`,`sheet_music_id`),
  KEY `students_studentfavo_sheet_music_id_b9085f95_fk_courses_s` (`sheet_music_id`),
  CONSTRAINT `students_studentfavo_sheet_music_id_b9085f95_fk_courses_s` FOREIGN KEY (`sheet_music_id`) REFERENCES `courses_sheetmusic` (`id`),
  CONSTRAINT `students_studentfavo_student_id_86b08821_fk_students_` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_studentfavorite`
--

LOCK TABLES `students_studentfavorite` WRITE;
/*!40000 ALTER TABLE `students_studentfavorite` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_studentfavorite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teachers_privacysetting`
--

DROP TABLE IF EXISTS `teachers_privacysetting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teachers_privacysetting` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `phone_visibility` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email_visibility` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `bio_visibility` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `teacher_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `teachers_privacysett_teacher_id_e48ea181_fk_teachers_` FOREIGN KEY (`teacher_id`) REFERENCES `teachers_teacherprofile` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teachers_privacysetting`
--

LOCK TABLES `teachers_privacysetting` WRITE;
/*!40000 ALTER TABLE `teachers_privacysetting` DISABLE KEYS */;
INSERT INTO `teachers_privacysetting` VALUES (1,'self','self','all',1);
/*!40000 ALTER TABLE `teachers_privacysetting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teachers_teacherprofile`
--

DROP TABLE IF EXISTS `teachers_teacherprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teachers_teacherprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `avatar` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bio` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `specialties` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `teachers_teacherprofile_user_id_c69bee92_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teachers_teacherprofile`
--

LOCK TABLES `teachers_teacherprofile` WRITE;
/*!40000 ALTER TABLE `teachers_teacherprofile` DISABLE KEYS */;
INSERT INTO `teachers_teacherprofile` VALUES (1,'yaobowen','男','17546096013','teachers/avatars/证件照一寸.jpg','','[]','2025-04-01 13:07:26.149874','2025-04-02 06:08:32.456786',2),(2,'lulix','','','','','[]','2025-04-12 17:12:59.361940','2025-04-12 17:12:59.361940',6);
/*!40000 ALTER TABLE `teachers_teacherprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user`
--

DROP TABLE IF EXISTS `users_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `user_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `avatar` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user`
--

LOCK TABLES `users_user` WRITE;
/*!40000 ALTER TABLE `users_user` DISABLE KEYS */;
INSERT INTO `users_user` VALUES (1,'pbkdf2_sha256$600000$eLojVhvSv2sQ90kXC2cCJ4$dzWtHeZeLH0cUmdDtRxhjUnfHuvdYx4nZ3n9uvIE63I=','2025-04-09 14:31:50.628335',1,'admin','','','505340458@qq.com',1,1,'2025-04-01 12:47:10.260054','admin','',''),(2,'pbkdf2_sha256$600000$39LnkgFQJKUReGrVpokwmR$MSmf/Bglz7I7HIlQyaDZL9jVKwmJPlSsZR999qP43Gg=','2025-04-14 08:46:21.025265',0,'yaobowen','','','505340458@qq.com',0,1,'2025-04-01 12:55:35.279628','teacher','',''),(3,'pbkdf2_sha256$600000$xZKmMxo32sb4AB9at6xrqe$nkhP+Gklbk0X2ect2Sk17XYX0ctgR2tbO6tJf0MmQk4=','2025-04-12 21:35:46.430946',0,'张三','','','',0,1,'2025-04-01 12:56:22.913023','student','','avatars/证件照一寸.jpg'),(4,'pbkdf2_sha256$600000$HXbFAkmvSGivtMaDofRfxS$akTdvM2xIlQhBpOlu+JhPbiH/tnfV+hHxed31W4RlhM=','2025-04-09 14:37:42.590652',0,'李四','','','',0,1,'2025-04-02 04:44:19.564041','student','','avatars/1.jpg'),(5,'pbkdf2_sha256$600000$frzWgSmnm81OGjKCuYFnH8$SmiX02sBAz5QJTwYPiLdt2zpTz03UxnoqSvxrERBs+g=','2025-04-09 15:44:47.367824',0,'王止舟','','','',0,1,'2025-04-06 10:18:44.892187','student','',''),(6,'pbkdf2_sha256$600000$Sojt7OYahZQSWWtFIys26A$RIGf4K3WTtSkXvrKtm0N8Q3BG/Nnqg1tKXBHFc0eLgs=',NULL,0,'lulix','','','',0,1,'2025-04-12 17:12:59.186073','teacher','','');
/*!40000 ALTER TABLE `users_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user_groups`
--

DROP TABLE IF EXISTS `users_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_groups_user_id_group_id_b88eab82_uniq` (`user_id`,`group_id`),
  KEY `users_user_groups_group_id_9afc8d0e_fk_auth_group_id` (`group_id`),
  CONSTRAINT `users_user_groups_group_id_9afc8d0e_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `users_user_groups_user_id_5f6f5a90_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user_groups`
--

LOCK TABLES `users_user_groups` WRITE;
/*!40000 ALTER TABLE `users_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_user_user_permissions`
--

DROP TABLE IF EXISTS `users_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_user_user_permissions_user_id_permission_id_43338c45_uniq` (`user_id`,`permission_id`),
  KEY `users_user_user_perm_permission_id_0b93982e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `users_user_user_perm_permission_id_0b93982e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `users_user_user_permissions_user_id_20aca447_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_user_user_permissions`
--

LOCK TABLES `users_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `users_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-14 16:46:37
