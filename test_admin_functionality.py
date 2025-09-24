#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности административной панели
"""

import sys
import os
import tempfile
import shutil

# Добавляем путь к проекту
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Проверка корректности импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        from database import (
            init_db, get_categories, get_products_by_category, get_product,
            add_product, update_product, delete_product, remove_from_cart_by_product
        )
        print("✅ Database functions imported successfully")
    except ImportError as e:
        print(f"❌ Database import error: {e}")
        return False
    
    try:
        from handlers.admin_handlers import (
            show_admin_menu, handle_admin_menu, log_admin_action,
            validate_price, validate_text_field, MESSAGES
        )
        print("✅ Admin handlers imported successfully")
    except ImportError as e:
        print(f"❌ Admin handlers import error: {e}")
        return False
    
    try:
        from handlers.states import admin_states
        print("✅ Admin states imported successfully")
    except ImportError as e:
        print(f"❌ Admin states import error: {e}")
        return False
    
    return True

def test_validation_functions():
    """Проверка функций валидации"""
    print("\n🧪 Тестирование функций валидации...")
    
    from handlers.admin_handlers import validate_price, validate_text_field
    
    # Тест валидации цены
    test_cases_price = [
        ("100", True, 100.0),
        ("100.50", True, 100.5),
        ("100,50", True, 100.5),
        ("0", False, 0.0),
        ("-10", False, 0.0),
        ("abc", False, 0.0),
        ("", False, 0.0)
    ]
    
    for price_str, expected_valid, expected_value in test_cases_price:
        is_valid, value = validate_price(price_str)
        if is_valid == expected_valid and (not expected_valid or abs(value - expected_value) < 0.001):
            print(f"✅ Price validation '{price_str}': {is_valid}, {value}")
        else:
            print(f"❌ Price validation '{price_str}': expected {expected_valid}, {expected_value}, got {is_valid}, {value}")
    
    # Тест валидации текста
    test_cases_text = [
        ("Valid text", True),
        ("", False),
        ("   ", False),
        ("A", True),
        ("A" * 255, True),
        ("A" * 256, False)
    ]
    
    for text, expected in test_cases_text:
        result = validate_text_field(text)
        if result == expected:
            print(f"✅ Text validation '{text[:20]}...': {result}")
        else:
            print(f"❌ Text validation '{text[:20]}...': expected {expected}, got {result}")

def test_database_operations():
    """Проверка операций с базой данных"""
    print("\n💾 Тестирование операций с базой данных...")
    
    # Создаем временную копию базы данных для тестирования
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    try:
        # Подменяем путь к базе данных
        import database
        original_db_path = 'music_bot.db'
        
        # Патчим функции для использования временной базы
        def patch_db_connect():
            return __import__('sqlite3').connect(temp_db.name)
        
        original_connect = database.sqlite3.connect
        database.sqlite3.connect = patch_db_connect
        
        # Инициализируем базу данных
        database.init_db()
        print("✅ Database initialized")
        
        # Получаем категории
        categories = database.get_categories()
        print(f"✅ Categories retrieved: {len(categories)} found")
        
        if categories:
            category_id = categories[0][0]
            
            # Тестируем добавление товара
            test_product_name = "Test Product"
            test_price = 1000.0
            test_description = "Test Description"
            
            database.add_product(test_product_name, category_id, test_price, test_description)
            print("✅ Product added successfully")
            
            # Проверяем, что товар добавился
            products = database.get_products_by_category(category_id)
            test_product_found = any(prod[1] == test_product_name for prod in products)
            if test_product_found:
                print("✅ Product found in category")
            else:
                print("❌ Product not found after adding")
            
            # Тестируем обновление товара
            database.update_product(test_product_name, category_id, "price", 2000.0)
            print("✅ Product updated successfully")
            
            # Проверяем обновление
            updated_products = database.get_products_by_category(category_id)
            updated_product = next((prod for prod in updated_products if prod[1] == test_product_name), None)
            if updated_product and updated_product[2] == 2000.0:
                print("✅ Product price updated correctly")
            else:
                print("❌ Product price not updated correctly")
            
            # Тестируем каскадное удаление
            database.remove_from_cart_by_product(test_product_name, category_id)
            print("✅ Cascade deletion from carts completed")
            
            # Тестируем удаление товара
            database.delete_product(test_product_name, category_id)
            print("✅ Product deleted successfully")
            
            # Проверяем удаление
            final_products = database.get_products_by_category(category_id)
            test_product_still_exists = any(prod[1] == test_product_name for prod in final_products)
            if not test_product_still_exists:
                print("✅ Product successfully removed from database")
            else:
                print("❌ Product still exists after deletion")
        
        # Восстанавливаем оригинальную функцию
        database.sqlite3.connect = original_connect
        
    except Exception as e:
        print(f"❌ Database operations error: {e}")
    finally:
        # Удаляем временную базу данных
        try:
            os.unlink(temp_db.name)
        except:
            pass

def test_message_constants():
    """Проверка констант сообщений"""
    print("\n📝 Тестирование констант сообщений...")
    
    from handlers.admin_handlers import MESSAGES
    
    required_messages = [
        'success_product_updated',
        'success_product_added', 
        'success_product_deleted',
        'error_category_not_found',
        'error_invalid_price',
        'error_empty_field',
        'confirm_deletion'
    ]
    
    for msg_key in required_messages:
        if msg_key in MESSAGES:
            print(f"✅ Message '{msg_key}' found: {MESSAGES[msg_key][:30]}...")
        else:
            print(f"❌ Message '{msg_key}' missing")

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск комплексного тестирования административного функционала\n")
    
    # Проверка импортов
    if not test_imports():
        print("❌ Import tests failed. Stopping.")
        return False
    
    # Проверка валидации
    test_validation_functions()
    
    # Проверка операций с БД
    test_database_operations()
    
    # Проверка констант
    test_message_constants()
    
    print("\n🎉 Тестирование завершено!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)