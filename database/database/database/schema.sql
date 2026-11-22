CREATE DATABASE IF NOT EXISTS delivery_tracking;
USE delivery_tracking;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('Admin', 'Staff') NOT NULL DEFAULT 'Staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS drivers (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    licence_number VARCHAR(50) NOT NULL UNIQUE,
    availability ENUM('Available', 'Unavailable') NOT NULL DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    driver_id INT DEFAULT NULL,
    delivery_address TEXT NOT NULL,
    delivery_date DATE NOT NULL,
    expected_delivery_date DATE DEFAULT NULL,
    status ENUM('Pending', 'Assigned', 'In Transit', 'Delivered', 'Failed')
        NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME DEFAULT NULL,
    CONSTRAINT fk_delivery_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_delivery_driver FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id),
    INDEX idx_delivery_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS delivery_updates (
    update_id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('Pending', 'Assigned', 'In Transit', 'Delivered', 'Failed')
        NOT NULL,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_update_delivery FOREIGN KEY (delivery_id)
        REFERENCES deliveries(delivery_id),
    CONSTRAINT fk_update_user FOREIGN KEY (user_id)
        REFERENCES users(user_id),
    INDEX idx_update_delivery (delivery_id),
    INDEX idx_update_status (status)
) ENGINE=InnoDB;
